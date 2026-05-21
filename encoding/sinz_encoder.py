
from pysat.solvers import Glucose3

class SinzCardinalityEncoder:
    def __init__(self, start_var: int = 1):
    

        self.next_var = start_var
        self.aux_vars = {}

    # ============================================================
    # PUBLIC API
    # ============================================================

    def amk(
        self,
        g: Glucose3,
        vars: list[int],
        k: int
    ) -> int:
      
        n = len(vars)

        if k < 0:
            g.add_clause([])
            return self.next_var

        if k >= n:
            return self.next_var

        if k == 0:
            for x in vars:
                g.add_clause([-x])
            return self.next_var

        # (1) ¬x_i ∨ s(i,1)
        for i in range(n - 1):

            x_i = vars[i]
            s_i1 = self._s(i, 0)

            g.add_clause([-x_i, s_i1])

        # (2) ¬s(i-1,j) ∨ s(i,j)
        for i in range(1, n - 1):

            for j in range(min(i, k)):

                s_prev = self._s(i - 1, j)
                s_curr = self._s(i, j)

                g.add_clause([-s_prev, s_curr])

        # (3) ¬x_i ∨ ¬s(i-1,j-1) ∨ s(i,j)
        for i in range(1, n - 1):

            for j in range(1, min(i + 1, k)):

                x_i = vars[i]

                s_prev = self._s(i - 1, j - 1)
                s_curr = self._s(i, j)

                g.add_clause([-x_i, -s_prev, s_curr])

        # (4) ¬x_i ∨ ¬s(i-1,k)
        for i in range(k, n):

            x_i = vars[i]
            s_prev_k = self._s(i - 1, k - 1)

            g.add_clause([-x_i, -s_prev_k])

        self.aux_vars.clear()

        return self.next_var
    

    def alk(
        self,
        g: Glucose3,
        vars: list[int],
        k: int
    ) -> int:
        n = len(vars)

        # --------------------------------------------------------
        # Trivial cases
        # --------------------------------------------------------

        if k <= 0:
            return

        if k > n:
            g.add_clause([])
            return


        negated_vars = [-x for x in vars]

        self.amk(
            g=g,
            vars=negated_vars,
            k=n - k
        )
        
        self.aux_vars.clear()
        return self.next_var 


    def exk(
        self,
        g: Glucose3,
        vars: list[int],
        k: int
    ) -> int:
        """
        Encode Exactly-K constraint.

        Sum(vars) == k
        """

        self.amk(g, vars, k)
        self.alk(g, vars, k)
        return self.next_var 
    # ============================================================
    # AUXILIARY VARIABLES
    # ============================================================

    def _s(
        self,
        i: int,
        j: int
    ) -> int:
        """
        Sequential counter variable.

        s(i,j) means:
        among x1..x(i+1),
        at least j variables are True.
        """

        key = (i, j)

        if key not in self.aux_vars:

            self.aux_vars[key] = self.next_var
            self.next_var += 1

        return self.aux_vars[key]
    
def main():

    g = Glucose3()

    vars = list(range(1, 11))
    k = 5
    encoder = SinzCardinalityEncoder(12)
    encoder.exk(g, vars, k)

    #gán 1 số biến true để kiểm tra 
    g.add_clause([4])
   
    
    result = g.solve()

    print("SAT:", result)

    if result:

        model = g.get_model()
        true_vars = [x for x in model if x > 0]
        print("Biến nhận giá trị 1:")
        print(true_vars)

if __name__ == "__main__":
    main()