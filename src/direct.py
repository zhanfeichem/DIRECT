import numpy as np
import _hilbert

class GlobalMin():
    def __init__(self, minimize=True, known=False, val=None):
        self.minimize = minimize
        self.known    = known
        self.value    = val


class Rectangle():
    def __init__(self, center, f_val, sides):
        self.center  = center
        self.f_val   = f_val
        self.sides   = sides
        self.__str__ = f_val

    @property
    def d2(self):    # size
        return np.sum((self.sides / 2.) ** 2)


class Direct():
    def __init__(self, f, bounds, epsilon=1e-4, max_feval=200, max_iter=10, max_rectdiv=100, globalmin=GlobalMin(), tol = 1e-2, bits = 5):
        self.epsilon       = epsilon  # global/local weight parameter
        self.max_feval     = max_feval
        self.max_iter      = max_iter
        self.max_rectdiv   = max_rectdiv
        self.globalmin     = globalmin
        self.tolerance     = tol      # allowable relative error if globalmin is known
        self.scale         = bounds[:,1] - bounds[:,0]
        self.shift         = bounds[:,0]
        self.n_feval       = 1
        self.n_rectdiv     = 0
        self.n_iter        = 0
        self.d_rect        = {}
        self.TERMINATE     = False
        # nD hyper-cube of side R = 2^bits
        self.D             = bounds.shape[0]
        self.bits          = bits
        self.N             = 2 ** (bits * self.D) # number of cells = R^nD
        if not self.globalmin.minimize:  # means maximization problem
            self.f_wrap = lambda x: -f(x)
        else:
            self.f_wrap = f
        assert isinstance(bounds, np.ndarray)
        assert np.all(self.scale > 0.)

    def true_sign(self, val):
        return val if self.globalmin.minimize else -val
    
    def divide_rectangle(self, po_rect):
        maxlen      = np.max(po_rect.sides)
        gap         = maxlen / 3.
#         gap         = maxlen / 2. ** self.D
        d_new_rects = {}
        self.d_rect[po_rect.d2].remove(po_rect)    # dict[key].remove(val) - removes key, val
        maxlen_sides = list(np.nonzero(po_rect.sides == maxlen)[0]) # only the longest sides are divided
        # evaluate points near center
        for side_idx in maxlen_sides:
            d_new_rects[side_idx]  = []
            new_center_u           = po_rect.center.copy()
#             new_center_u           = self.l2u(po_rect.center)
            new_center_u[side_idx] += gap
            new_fval_u             = self.f_wrap(self.u2r(new_center_u))
#             d_new_rects[side_idx].append(Rectangle(self.u2l(new_center_u), new_fval_u, po_rect.sides.copy()))
            d_new_rects[side_idx].append(Rectangle(new_center_u, new_fval_u, po_rect.sides.copy()))

            if new_fval_u < self.curr_opt:
                self.curr_opt      = new_fval_u
                self.x_at_opt      = self.u2r(new_center_u)
            self.n_feval += 1

            if self.globalmin.known:
                if self.globalmin.value:
                    error = (self.curr_opt - self.globalmin.value)/abs(self.globalmin.value)
                else:   error = self.curr_opt
                if error < self.tolerance:
                    self.TERMINATE = True
                    return
            elif self.n_feval >= self.max_feval or self.n_rectdiv >= self.max_rectdiv:
                self.TERMINATE = True
                return

            new_center_l           = po_rect.center.copy()
#             new_center_l           = self.l2u(po_rect.center)
            new_center_l[side_idx] -= gap
            new_fval_l             = self.f_wrap(self.u2r(new_center_l))
#             d_new_rects[side_idx].append(Rectangle(self.u2l(new_center_l), new_fval_l, po_rect.sides.copy()))
            d_new_rects[side_idx].append(Rectangle(new_center_l, new_fval_l, po_rect.sides.copy()))

            if new_fval_l < self.curr_opt:
                self.curr_opt      = new_fval_l
                self.x_at_opt      = self.u2r(new_center_l)
            self.n_feval += 1
            if self.globalmin.known:
                if self.globalmin.value:
                    error = (self.curr_opt - self.globalmin.value)/abs(self.globalmin.value)
                else:   error = self.curr_opt
                if error < self.tolerance:
                    self.TERMINATE = True
                    return
            elif self.n_feval >= self.max_feval or self.n_rectdiv >= self.max_rectdiv:
                self.TERMINATE = True
                return

        # axis with better function value get divided first
        maxlen_sides = sorted(maxlen_sides, key=lambda x: min([t.f_val for t in d_new_rects[x]]))
        for i in range(len(maxlen_sides)):
            self.n_rectdiv += 1
            for each_rect in d_new_rects[maxlen_sides[i]]:
                for j in range(i+1):  # check if the length should be divided
                    each_rect.sides[maxlen_sides[j]] /= 3.
#                     each_rect.sides[maxlen_sides[j]] /= 2.
        for side_idx in maxlen_sides:  # po_rect gets divided in every (longest) dimension
#             po_rect.sides[side_idx] /= 2.
            po_rect.sides[side_idx] /= 3.
        for l_rect in d_new_rects.values():
            for each_rect in l_rect:
                if each_rect.d2 not in self.d_rect:
                    self.d_rect[each_rect.d2] = [each_rect]
                elif each_rect.f_val < self.d_rect[each_rect.d2][0].f_val:
                    self.d_rect[each_rect.d2].insert(0, each_rect)
                else:
                    self.d_rect[each_rect.d2].append(each_rect)
        # insert po_rect
        if po_rect.d2 not in self.d_rect:
            self.d_rect[po_rect.d2] = [po_rect]
        elif po_rect.f_val < self.d_rect[po_rect.d2][0].f_val:
            self.d_rect[po_rect.d2].insert(0, po_rect)
        else:
            self.d_rect[po_rect.d2].append(po_rect)
        # remove empty lists from the dictionary
        for dd in [key for key in self.d_rect if len(self.d_rect[key]) == 0]:
            self.d_rect.pop(dd)

    def calc_lbound(self, border):
        lb     = np.zeros(len(border))
        border = np.array(border)
        for i in range(len(border)):
            tmp_rects = [j for j, val in enumerate(border[:,0]) if val < border[i,0]]
            if len(tmp_rects):
                lb[i] = max((border[i,1] - border[tmp_rects,1])/(border[i,0] - border[tmp_rects,0]))
            else:    lb[i] = -1.976e14
        return lb

    def calc_ubound(self, border):
        ub     = np.zeros(len(border))
        border = np.array(border)
        for i in range(len(border)):
            tmp_rects    = [j for j, val in enumerate(border[:,0]) if val > border[i,0]]    # size, f_val
            if len(tmp_rects):
                ub[i]    = min((border[tmp_rects,1] - border[i,1])/(border[tmp_rects,0] - border[i,0]))    # d(f_val)/d(size)
            else:   ub[i] = 1.976e14
        return ub

    def get_potentially_optimal_rects(self):
        border   = [(key, l[0].f_val) for key, l in self.d_rect.items()]    # border=[(d2, f_val)], d_rect={d2: Rectangle(c, f_val, s)}
        border   = sorted(border, key=lambda t:t[0])    # sort based on size, then f_val
        l_po_key = []    # store sizes
        final_l_po_key = []
        for i in range(len(border)):
            l_po_key.append(border[i][0])
        lbound   = self.calc_lbound(border)
        ubound   = self.calc_ubound(border)
        maybe_po = [i for i in range(len(border)) if lbound[i] <= ubound[i]]    # indices of hull satisfying first condition
        po = [] # indices of hull satisfying second condition
        for j in range(len(maybe_po)):
            if self.curr_opt:
                cond = (self.curr_opt - border[maybe_po[j]][1] + border[maybe_po[j]][0]*ubound[maybe_po[j]])/abs(self.curr_opt)
                if cond >= self.epsilon:    po.append(j)
            else:
                cond = border[maybe_po[j]][-1] - border[maybe_po[j]][0]*ubound[maybe_po[j]]
                if cond <= 0:   po.append(j)
        for i in range(len(po)):
            final_l_po_key.append(l_po_key[maybe_po[po[i]]])
        return [self.d_rect[key][0] for key in final_l_po_key]    # return rectangles

    def u2l(self, unit_coord):
        real = (unit_coord * 32.).astype(int).tolist()
        return _hilbert.coordinates_to_distance(real, self.bits, self.D)

    def u2r(self, unit_coord):
        """unit to real: map a coordinate in unit hyper-cube to one in the actual rectangle"""
        return unit_coord * self.scale + self.shift

    def l2u(self, l):
        #TODO: make scale and shift generic for all dimensions
        #TODO: what if bits*D is not even :(
        """line to unit: map a position on the Hilbert curve to a coordinate in unit hyper-cube"""
        coord = np.array(_hilbert.distance_to_coordinates(l, self.bits, self.D))
        return coord / 32.

    def l2r(self, l):
        """line to real: map a position on the Hilbert curve to a coordinate in the actual rectangle"""
        return self.u2r(self.l2u(l))

    def run(self, file):
        s                    = np.array([1.]*self.D)    # rectangle sides, unit length
#         l                    = self.N // 2
        c                    = np.array([0.5]*self.D)
#         f_val                = self.f_wrap(self.l2r(l))
        f_val                = self.f_wrap(self.u2r(c))
#         self.x_at_opt        = self.l2r(l)
        self.x_at_opt        = self.u2r(c)
#         rect                 = Rectangle(l, f_val, s)
        rect                 = Rectangle(c, f_val, s)
        self.d_rect[rect.d2] = [rect]
        self.curr_opt        = f_val
        while not self.TERMINATE and (self.globalmin.known or self.n_iter <= self.max_iter):
            self.n_iter += 1
            for po_rect in self.get_potentially_optimal_rects():    # select potentially optimal rectangles
                if not self.TERMINATE:
                    # identify longest side(s) of po_rect
                    # evaluate the f(new c)s
                    # divide po_rect into smaller rectangles
                    # update curr_opt, x_at_opt, n_feval
                    self.divide_rectangle(po_rect)

        print("number of function evaluations =", self.n_feval)
#         file.write("number of function evaluations = " + str(self.n_feval) + "\n")
        opt, x = self.true_sign(self.curr_opt), self.x_at_opt
        print("optimum =", opt, ", x =", x, "\n")
#         file.write("optimum = " + str(opt) + ",  x = " + str(x) + "\n\n")