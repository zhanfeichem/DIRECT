from direct import Direct, GlobalMin
from helper import *

import datetime
import traceback

if __name__ == "__main__":
# Direct parameter list:
# f, bounds, epsilon=1e-4, max_feval=200, max_iter=10, max_rectdiv=200,
# globalmin=GlobalMin(minimize=True, known=False, val=0.), tol=1e-2, bits=5

    try:
        with open("direct-run.log", 'a') as file:
#            file.write("=================================================\n")
#            file.write("RUN MAIN.PY "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"\n")
         
            print('test Goldstein-Price results:')
#            file.write('test Goldstein-Price results:\n')
            Direct(func1, bounds=np.array([[-2,2],[-2,2]]), globalmin=GlobalMin(known=True, val=3.)).run(file)
       
            print('test Rosenbrock results:')
#            file.write('test Rosenbrock results:\n')
            Direct(func2, bounds=np.array([[-5,5],[-2,8]]), globalmin=GlobalMin(known=True, val=0.)).run(file)
          
            print('test Six-hump Camelback results:')
#            file.write('test Six-hump Camelback results:\n')
            Direct(func3, bounds=np.array([[-3,2],[-3,2]]), globalmin=GlobalMin(known=True, val=-1.031628453489877)).run(file)
       
            print('test Rastrigin results:')
#            file.write('test Rastrigin results:\n')
            Direct(func4, bounds=np.array([[-1,1],[-1,1]]), globalmin=GlobalMin(known=True, val=-2.)).run(file)
      
            print('test Griewank results:')
#            file.write('test Griewank results:\n')
            Direct(func5, bounds=np.array([[-600,600],[-600,600]]), globalmin=GlobalMin(known=True, val=0.)).run(file)
#            Direct(func5, bounds=np.array([[-600,600]]*10), globalmin=GlobalMin(known=True, val=0.)).run(file)

            print('test Hartmann results:')
#            file.write('test Griewank results:\n')
            Direct(func6, bounds=np.array([[0,1]]*6), globalmin=GlobalMin(known=True, val=-3.32237)).run(file)

        file.close()
    except Exception:
        traceback.print_exc()