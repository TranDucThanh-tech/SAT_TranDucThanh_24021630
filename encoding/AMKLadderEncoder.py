import math
from pysat.solvers import Glucose3

class AMKLadderEncoder:
    def __init__(self, start_id=1):
        self.dictionary_id = {}
        self.next_id = [start_id]

    def _key_sc_var(self, i, j, s):
        """Tạo key cho biến phụ R."""
        return f"{i}_{j}_{s}"

    def get_sc_var(self, i, j, s):
        """Lấy hoặc tạo ID mới cho biến phụ R_{i,j,s}."""
        key = self._key_sc_var(i, j, s)
        if key in self.dictionary_id:
            return self.dictionary_id[key]

        self.dictionary_id[key] = self.next_id[0]
        self.next_id[0] += 1
        return self.dictionary_id[key]

    def get_number_block(self, number_of_area, is_first, weight):
        """Xác định số thứ tự của Block từ Area."""
        number_of_block = 2 * number_of_area
        if is_first:
            number_of_block -= 1
        return number_of_block

    def encode_amk_block(self, solver, block, number_block, k):
        """Mã hóa AMK cho một Block đơn lẻ bằng Sequential Counter."""
        w = len(block)
        
        # 1. Các công thức khẳng định (Positive clauses)
        for j in range(0, w - 1):
            x_ij = block[j]
            r_ij1 = self.get_sc_var(number_block, j, 0)
            solver.add_clause([-x_ij, r_ij1])
        
        for j in range(1, w - 1):
            for s in range(0, min(j, k)):
                r_ijm1s = self.get_sc_var(number_block, j - 1, s)
                r_ijs = self.get_sc_var(number_block, j, s)
                solver.add_clause([-r_ijm1s, r_ijs])

        for j in range(1, w - 1):
            for s in range(1, min(j + 1, k)):
                x_ij = block[j]
                r_ijm1sm1 = self.get_sc_var(number_block, j - 1, s - 1)
                r_ijs = self.get_sc_var(number_block, j, s)
                solver.add_clause([-x_ij, -r_ijm1sm1, r_ijs])

        # 2. Các công thức phủ định để tránh biến "ảo"
        for j in range(0, k):
            x_ij = block[j]
            r_ijj = self.get_sc_var(number_block, j, j)
            solver.add_clause([x_ij, -r_ijj])

        for j in range(1, w - 1):
            for s in range(1, min(j + 1, k)):
                r_ijm1sm1 = self.get_sc_var(number_block, j - 1, s - 1)
                r_ijs = self.get_sc_var(number_block, j, s)
                solver.add_clause([r_ijm1sm1, -r_ijs])

        for j in range(1, w - 1):
            for s in range(0, min(j, k)):
                x_ij = block[j]
                r_ijm1s = self.get_sc_var(number_block, j - 1, s)
                r_ijs = self.get_sc_var(number_block, j, s)
                solver.add_clause([x_ij, r_ijm1s, -r_ijs])

        # 3. Công thức ràng buộc (Constraint clauses)
        for j in range(k, w):
            x_ij = block[j]
            r_ijm1k = self.get_sc_var(number_block, j - 1, k - 1)
            solver.add_clause([-x_ij, -r_ijm1k])

    def connect_areas(self, solver, area1_idx, area2_idx, k, weight):
        """Nối các Area để đảm bảo tổng liên hoàn không vượt quá k."""
        num_block1 = self.get_number_block(area1_idx, False, weight)
        num_block2 = self.get_number_block(area2_idx, True, weight)
        
        for j in range(2, weight + 1):
            for p in range(1, k + 1):
                j1, s1 = (weight - j), (k - p)
                j2, s2 = (j - 2), (p - 1)

                if s1 >= 0 and s2 >= 0:
                    r_var1 = self.get_sc_var(num_block1, j1, s1)
                    r_var2 = self.get_sc_var(num_block2, j2, s2)
                    solver.add_clause([-r_var1, -r_var2])

    def apply(self, solver, variables, k, weight):
        """Hàm chính thực hiện mã hóa toàn bộ chuỗi biến."""
        n_areas = math.ceil(len(variables) / weight)
        
        # Cập nhật ID bắt đầu cho biến phụ để không trùng với biến đầu vào
        if self.next_id[0] <= max(variables):
            self.next_id[0] = max(variables) + 1

        # Chia và Encoding từng Area
        for idx in range(n_areas):
            start = weight * idx
            end = min(start + weight, len(variables))
            area_vars = variables[start:end]
            
            # Khởi tạo Block xuôi và ngược
            num_b1 = self.get_number_block(idx, True, weight)
            num_b2 = self.get_number_block(idx, False, weight)
            
            if idx != 0:
                self.encode_amk_block(solver, area_vars, num_b1, k)
            if idx != n_areas - 1:
                self.encode_amk_block(solver, area_vars[::-1], num_b2, k)

        # Nối các Area lại với nhau
        for idx in range(n_areas - 1):
            self.connect_areas(solver, idx, idx + 1, k, weight)

# --- Ví dụ sử dụng ---
if __name__ == "__main__":
    solver = Glucose3()
    vars_list = list(range(1, 11)) # X1 đến X10
    k_val = 2
    w_val = 4
    
    encoder = AMKLadderEncoder()
    encoder.apply(solver, vars_list, k_val, w_val)
    
    # Giả sử ép X2 = True (ID là 2)
    solver.add_clause([2])
    
    if solver.solve():
        print("SAT: Tìm thấy bộ giá trị thỏa mãn")
        model = solver.get_model()
        true_vars = [x for x in model if x > 0 and x <= 10]
        print(f"Các biến X nhận giá trị 1: {true_vars}")
    else:
        print("UNSAT")
        