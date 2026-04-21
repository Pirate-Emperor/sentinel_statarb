PROGRAM_NAME=BS_sor
OBJECTS=BS_SOR_main.o SentSOR.o PDE_solver.o       

CXX=clang #gcc


CXXFLAGS +=-Wall -Werror -O2
LIBS=-lm                  




$(PROGRAM_NAME):$(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $(PROGRAM_NAME) $(OBJECTS) $(LIBS)

	@echo " "
	@echo "Compilation completed!"
	@echo " "



BS_SOR_main.o:SentSOR.h PDE_solver.h BS_SOR_main.c  
	$(CXX) $(CXXFLAGS) -c -o BS_SOR_main.o BS_SOR_main.c


SentSOR.o:SentSOR.h SentSOR.c 
	$(CXX) $(CXXFLAGS) -c -o SentSOR.o SentSOR.c


PDE_solver.o:SentSOR.h SentSOR.c PDE_solver.h PDE_solver.c 
	$(CXX) $(CXXFLAGS) -c -o PDE_solver.o PDE_solver.c



clean:
	rm -f *.o
	rm -f *~
	rm -f core


cat: 
	cat Makefile


all:	$(PROGRAM_NAME) clean


