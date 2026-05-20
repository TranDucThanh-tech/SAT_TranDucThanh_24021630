from math import ceil
from pysat.solvers import Glucose3


class LadderEncoder:

    def __init__(self, start_id: int):
        self.next_id = start_id
        self.var_map = {}


    def ladder_amk( 
            self, 
            g: Glucose3, 
            vars: list[int], 
            k: int, 
            weight: int) -> int:

        n_vars = len(vars)
        n_areas = ceil(n_vars / weight)
        

        # Encode each area
        for area_id in range(n_areas):
            area = self._get_area(vars, weight, area_id)

            self._encode_area(
                g=g, 
                area=area, 
                area_id=area_id, 
                k=k, 
                n_areas=n_areas, 
                weight=weight)

        # Connect neighboring areas
        for area_id in range(n_areas - 1):
            self._connect_areas(
                g=g, 
                area1_id=area_id, 
                area2_id=area_id + 1, 
                k=k, 
                weight=weight)
            
        self.var_map.clear()
        return  self.next_id
   
    def ladder_alk(
        self,
        g: Glucose3,
        vars: list[int],
        k: int,
        weight: int
    ) -> int:
        
        negated_vars = [-x for x in vars]
        self.ladder_amk(
            g=g,
            vars=negated_vars,
            k = weight - k,
            weight = weight
        )
        self.var_map.clear()
        return self.next_id

    def ladder_exk(
        self,
        g: Glucose3,
        vars: list[int],
        k: int,
        weight: int
    ) -> int:
    
        self.ladder_amk(
            g=g,
            vars=vars,
            k=k,
            weight=weight
        )

        self.ladder_alk(
            g=g,
            vars=vars,
            k=k,
            weight=weight
        )
        return self.next_id


    def _get_area(
            self, 
            vars: list[int], 
            weight: int, 
            area_id: int) -> list[int]:
        start = weight * area_id
        end = min(start + weight, len(vars))
        return vars[start:end]

    def _encode_area(
        self,
        g: Glucose3,
        area: list[int],
        area_id: int,
        k: int,
        n_areas: int,
        weight: int
    ) -> None:

        forward_block = self._block_number(
            area_id,
            is_first=True
        )

        backward_block = self._block_number(
            area_id,
            is_first=False
        )

        forward_area = area
        backward_area = area[::-1]

        if n_areas == 1:
            self._amk(g, forward_area, forward_block, k)
            return

        if area_id != 0:
            self._amk(
                g,
                forward_area,
                forward_block,
                k
            )

        if area_id != n_areas - 1:
            self._amk(
                g,
                backward_area,
                backward_block,
                k
            )

    def _connect_areas(
    self,
    g: Glucose3,
    area1_id: int,
    area2_id: int,
    k: int,
    weight: int
) -> None:
        block1 = self._block_number(area1_id, is_first=False)
        block2 = self._block_number(area2_id, is_first=True)
        for j in range(2, weight + 1):
            for p in range(1, k + 1):

                j1 = weight - j
                s1 = k - p

                j2 = j - 2
                s2 = p - 1

                if j1 < 0 or j2 < 0 or s1 < 0 or s2 < 0:
                    continue

                r1 = self._sc_var(block1, j1, s1)
                r2 = self._sc_var(block2, j2, s2)
                
                g.add_clause([-r1, -r2])
                

    def _amk(
        self,
        g: Glucose3,
        block: list[int],
        block_id: int,
        k: int
    ) -> int:

        w = len(block)
        
        if w == 0:
            return
        
        if k >= w:
            k = w
        
        if k < 0:
            g.add_clause([]) 
            return

        if k == 0:
            for x in block:
                g.add_clause([-x])
            return


        for j in range(w):
            x_ij = block[j]
            r_ij1 = self._sc_var(block_id, j, 0)

            clause = [-x_ij, r_ij1]
            g.add_clause(clause)

        for j in range(1, w):
            for s in range(min(j, k)):

                r_prev = self._sc_var(block_id, j - 1, s)
                r_curr = self._sc_var(block_id, j, s)

                clause = [-r_prev, r_curr]
                g.add_clause(clause)


        for j in range(1, w):
            for s in range(1, min(j + 1, k)):

                x_ij = block[j]
                r_prev = self._sc_var(block_id, j - 1, s - 1)
                r_curr = self._sc_var(block_id, j, s)

                clause = [-x_ij, -r_prev, r_curr]
                g.add_clause(clause)

        for j in range(k):
            x_ij = block[j]
            r_jj = self._sc_var(block_id, j, j)

            clause = [x_ij, -r_jj]
            g.add_clause(clause)

        for j in range(1, w):
            for s in range(1, min(j + 1, k)):

                r_prev = self._sc_var(block_id, j - 1, s - 1)
                r_curr = self._sc_var(block_id, j, s)

                clause = [r_prev, -r_curr]
                g.add_clause(clause)

        for j in range(1, w):
            for s in range(min(j, k)):

                x_ij = block[j]
                r_prev = self._sc_var(block_id, j - 1, s)
                r_curr = self._sc_var(block_id, j, s)

                clause = [x_ij, r_prev, -r_curr]
                g.add_clause(clause)
               

        for j in range(k, w):
            x_ij = block[j]
            r_prev_k = self._sc_var(block_id, j - 1, k - 1)

            clause = [-x_ij, -r_prev_k]
            g.add_clause(clause)
           

    def _sc_var(
        self,
        block_id: int,
        j: int,
        s: int
    ) -> int:
        

        key = (block_id, j, s)

        if key not in self.var_map:
            self.var_map[key] = self.next_id
            self.next_id += 1

        return self.var_map[key]

    def _block_number(
        self,
        area_id: int,
        is_first: bool
    ) -> int:
        
        block_number = 2 * area_id

        if is_first:
            block_number -= 1

        return block_number
    
    
def main():
    g = Glucose3()
    vars = list(range(1, 16))
    weight = 14

    k = 4
    encoder = LadderEncoder(start_id = len(vars) + 1) 
    encoder.ladder_exk(g, vars, k, weight)
    
    
    result = g.solve()
    print("SAT:", result)

    if result:

        model = g.get_model()
        true_vars = [x for x in model if x > 0]
        print("Biến nhận giá trị 1:")
        print(true_vars)


if __name__ == "__main__":
    main()