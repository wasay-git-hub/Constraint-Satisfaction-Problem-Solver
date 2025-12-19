import re
import json
import copy

# configuration
KNOWN_NAMES = {
    "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Heidi",
    "Ivan", "Judy", "Mallory", "Niaj", "Olivia", "Peggy", "Sybil", "Trudy",
    "Victor", "Walter", "Oscar", "Plato", "Rosa", "Ted", "Sasha", "Yvonne",
    "Chuck", "Dan", "Erin", "Fay", "George", "Harry", "Iris", "John", "Karl",
    "Larry", "Mike", "Nancy", "Pat", "Quinn", "Ray", "Sam", "Tom", "Uma",
    "Violet", "Will", "Xena", "Yuri", "Zack", "Steve", "Karen", "Jim", "Pam"
}

STOPWORDS = {
    "The", "This", "That", "Three", "Four", "Five", "House", "Each", "If",
    "Clues", "Note", "Rules", "In", "On", "Of", "A", "An", "There", "Here",
    "Where", "Which", "When", "Then", "And", "Or", "Not", "But", "To", "From",
    "Left", "Right", "Immediately", "Next", "Adjacent", "Person", "Friend",
    "Man", "Woman", "Boy", "Girl", "Owner", "Pet", "Color", "House", "Lives",
    "Has", "Owns", "Is", "Are", "Was", "Were", "Be", "Been", "Being"
}

# enhanced logic engine with forward checking
class SolverEngine:
    def __init__(self, variables, domains, num_houses, categories):
        self.variables = variables
        self.domains = domains
        self.num_houses = num_houses
        self.categories = categories
        self.constraints = []
        self.steps = 0

    def add_constraint(self, type, vars, extra=None):
        self.constraints.append({"type": type, "vars": vars, "extra": extra})

    def propagate(self):
        """Enhanced propagation with multiple passes."""
        changed = True
        iterations = 0
        max_iterations = 1000

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            # Pass 1: Constraint propagation
            for c in self.constraints:
                t = c["type"]
                vs = c["vars"]

                if t == "eq":
                    s1, s2 = self.domains[vs[0]], self.domains[vs[1]]
                    common = s1.intersection(s2)
                    if len(common) < len(s1):
                        self.domains[vs[0]] = common
                        changed = True
                    if len(common) < len(s2):
                        self.domains[vs[1]] = common
                        changed = True

                elif t == "neq":
                    if len(self.domains[vs[0]]) == 1:
                        val = list(self.domains[vs[0]])[0]
                        if val in self.domains[vs[1]]:
                            self.domains[vs[1]].remove(val)
                            changed = True
                    if len(self.domains[vs[1]]) == 1:
                        val = list(self.domains[vs[1]])[0]
                        if val in self.domains[vs[0]]:
                            self.domains[vs[0]].remove(val)
                            changed = True

                elif t == "next":
                    valid_a = {v for v in self.domains[vs[0]]
                               if any(abs(v - vb) == 1 for vb in self.domains[vs[1]])}
                    if len(valid_a) < len(self.domains[vs[0]]):
                        self.domains[vs[0]] = valid_a
                        changed = True

                    valid_b = {v for v in self.domains[vs[1]]
                               if any(abs(v - va) == 1 for va in self.domains[vs[0]])}
                    if len(valid_b) < len(self.domains[vs[1]]):
                        self.domains[vs[1]] = valid_b
                        changed = True

                elif t == "left":
                    is_imm = c["extra"]
                    if is_imm:
                        valid_a = {v for v in self.domains[vs[0]] if (v + 1) in self.domains[vs[1]]}
                        valid_b = {v for v in self.domains[vs[1]] if (v - 1) in self.domains[vs[0]]}
                    else:
                        if self.domains[vs[1]]:
                            max_b = max(self.domains[vs[1]])
                            valid_a = {v for v in self.domains[vs[0]] if v < max_b}
                        else:
                            valid_a = set()
                        if self.domains[vs[0]]:
                            min_a = min(self.domains[vs[0]])
                            valid_b = {v for v in self.domains[vs[1]] if v > min_a}
                        else:
                            valid_b = set()

                    if len(valid_a) < len(self.domains[vs[0]]):
                        self.domains[vs[0]] = valid_a
                        changed = True
                    if len(valid_b) < len(self.domains[vs[1]]):
                        self.domains[vs[1]] = valid_b
                        changed = True

            # Pass 2: Category-based hidden singles
            for cat_name, cat_items in self.categories.items():
                for house in range(1, self.num_houses + 1):
                    candidates = [item for item in cat_items if house in self.domains[item]]
                    if len(candidates) == 1:
                        if len(self.domains[candidates[0]]) > 1:
                            self.domains[candidates[0]] = {house}
                            changed = True

            # Pass 3: if only one house left for a variable
            for v in self.variables:
                if len(self.domains[v]) == 1:
                    assigned_house = list(self.domains[v])[0]
                    # Remove from all other variables in same category
                    for cat_items in self.categories.values():
                        if v in cat_items:
                            for other in cat_items:
                                if other != v and assigned_house in self.domains[other]:
                                    self.domains[other].remove(assigned_house)
                                    changed = True

            # Safety check
            for v in self.variables:
                if not self.domains[v]:
                    return False

        return True

    def is_valid_assignment(self, var, val):
        """Forward checking: Test if assigning var=val leads to contradiction."""
        backup = copy.deepcopy(self.domains)
        self.domains[var] = {val}
        result = self.propagate()
        self.domains = backup
        return result

    def preprocess_with_forward_checking(self):
        """Apply forward checking to prune domains before search."""
        changed = True
        while changed:
            changed = False
            for var in self.variables:
                if len(self.domains[var]) > 1:
                    valid_values = []
                    for val in list(self.domains[var]):
                        if self.is_valid_assignment(var, val):
                            valid_values.append(val)

                    if len(valid_values) < len(self.domains[var]):
                        self.domains[var] = set(valid_values)
                        changed = True

                        # Re-propagate after pruning
                        if not self.propagate():
                            return False
        return True

    def validate_solution(self, solution):
        """Verify solution satisfies all constraints."""
        if not solution:
            return False

        # Check all variables assigned
        if len(solution) != len(self.variables):
            return False

        # Check all values in valid range
        for var, val in solution.items():
            if val < 1 or val > self.num_houses:
                return False

        # Check all constraints satisfied
        for c in self.constraints:
            t = c["type"]
            vs = c["vars"]

            if t == "eq":
                if solution[vs[0]] != solution[vs[1]]:
                    return False
            elif t == "neq":
                if solution[vs[0]] == solution[vs[1]]:
                    return False
            elif t == "next":
                if abs(solution[vs[0]] - solution[vs[1]]) != 1:
                    return False
            elif t == "left":
                if c["extra"]:  # immediately left
                    if solution[vs[0]] != solution[vs[1]] - 1:
                        return False
                else:
                    if solution[vs[0]] >= solution[vs[1]]:
                        return False

        # Check each category has all different values
        for cat_items in self.categories.values():
            values = [solution[item] for item in cat_items if item in solution]
            if len(values) != len(set(values)):
                return False

        return True

    def solve(self):
        self.steps = 0

        # Step 1: Initial propagation
        if not self.propagate():
            return None

        # Step 2: Forward checking preprocessing
        if not self.preprocess_with_forward_checking():
            return None

        # Step 3: Final propagation
        if not self.propagate():
            return None

        # Check if solved by propagation alone
        if all(len(self.domains[v]) == 1 for v in self.variables):
            solution = {v: list(self.domains[v])[0] for v in self.variables}
            if self.validate_solution(solution):
                return solution
            return None

        # Step 4: Backtracking with validation
        initial = {v: list(self.domains[v])[0] for v in self.variables if len(self.domains[v]) == 1}
        solution = self.backtrack(initial)

        # Validate before returning
        if self.validate_solution(solution):
            return solution
        return None

    def backtrack(self, assignment):
        self.steps += 1
        if self.steps > 50000:
            return None

        if len(assignment) == len(self.variables):
            return assignment

        # MRV heuristic
        unassigned = [v for v in self.variables if v not in assignment]
        var = min(unassigned, key=lambda v: len(self.domains[v]))

        original = copy.deepcopy(self.domains)

        # Try values in order
        values = sorted(list(self.domains[var]))

        for val in values:
            self.domains[var] = {val}

            if self.propagate():
                vars_to_add = []
                for v in self.variables:
                    if v not in assignment and len(self.domains[v]) == 1:
                        vars_to_add.append(v)

                for v in vars_to_add:
                    assignment[v] = list(self.domains[v])[0]
                assignment[var] = val

                if len(assignment) == len(self.variables):
                    return assignment

                result = self.backtrack(assignment)
                if result:
                    return result

                for v in vars_to_add:
                    del assignment[v]
                if var in assignment:
                    del assignment[var]

            self.domains = copy.deepcopy(original)

        return None


# ROBUST PARSING
def parse_and_solve(puzzle_text, puzzle_id):
    clean_text = puzzle_text.replace('"', '').replace("'", "")

    # 1. Grid Size - Multiple patterns
    num_houses = 3
    size_patterns = [
        (r'(\d+)\s+houses', int),
        (r'(\d+)\s+friends', int),
        (r'(three|3)\b', lambda x: 3),
        (r'(four|4)\b', lambda x: 4),
        (r'(five|5)\b', lambda x: 5),
    ]

    for pattern, converter in size_patterns:
        m = re.search(pattern, clean_text.lower())
        if m:
            try:
                num_houses = converter(m.group(1)) if callable(converter) else int(m.group(1))
                break
            except:
                pass

    # 2. Entity Extraction
    categories = {}
    known_entities = set()
    lines = clean_text.split('\n')

    for line in lines:
        if ':' in line and ',' in line and len(line) < 200:
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            cat = parts[0].strip()
            cat = re.sub(r'^\d+\.\s*', '', cat).strip()

            items = [x.strip().rstrip('.') for x in parts[1].split(',')]
            items = [x for x in items if x and len(x) > 1 and len(x) < 20]

            if len(items) >= num_houses:
                if cat.endswith('s') and cat.lower() not in ['class', 'glass']:
                    cat = cat[:-1]
                cat = cat.title()
                categories[cat] = items[:num_houses]
                known_entities.update(items[:num_houses])

    # 3. Name Extraction
    found_names = set()
    clues_part = clean_text
    if "Clues" in clean_text:
        clues_part = clean_text.split("Clues", 1)[1]

    for name in KNOWN_NAMES:
        if re.search(r'\b' + re.escape(name) + r'\b', clues_part, re.IGNORECASE):
            found_names.add(name)
            if len(found_names) >= num_houses:
                break

    # Scan for capitalized names
    cap_words = re.findall(r'\b[A-Z][a-z]+\b', clues_part)
    for word in cap_words:
        if word not in known_entities and word not in STOPWORDS:
            found_names.add(word)
            if len(found_names) >= num_houses:
                break

    if found_names:
        sorted_names = sorted(list(found_names))[:num_houses]
        if "Name" not in categories:
            categories["Name"] = sorted_names
            known_entities.update(sorted_names)

    # 4. Build variables
    all_vars = []
    for items in categories.values():
        all_vars.extend(items)

    if not all_vars:
        return json.dumps({"header": ["House"], "rows": []}), 0

    # 5. Setup solver
    house_domain = set(range(1, num_houses + 1))
    domains = {v: house_domain.copy() for v in all_vars}
    solver = SolverEngine(all_vars, domains, num_houses, categories)

    # AllDifferent
    for items in categories.values():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                solver.add_constraint("neq", [items[i], items[j]])

    # 6. Parse clues carefully
    clue_lines = re.split(r'\n\s*\d+\.\s*', clues_part)
    clues = [c.strip() for c in clue_lines if len(c.strip()) > 8]

    for clue in clues:
        try:
            parse_clue_robust(clue, all_vars, solver, num_houses)
        except:
            pass

    # 7. Solve
    solution = solver.solve()

    # 8. Format
    headers = ["House"]
    cats = list(categories.keys())
    if "Name" in cats:
        headers.append("Name")
        cats.remove("Name")
    cats.sort()
    headers.extend(cats)

    rows = []
    if solution:
        for i in range(1, num_houses + 1):
            row = [str(i)]
            for h in headers[1:]:
                found = ""
                if h in categories:
                    for item in categories[h]:
                        if item in solution and solution[item] == i:
                            found = item
                            break
                row.append(found)
            rows.append(row)
    else:
        rows = [["" for _ in headers] for _ in range(num_houses)]

    return json.dumps({"header": headers, "rows": rows}), solver.steps


def parse_clue_robust(clue, all_vars, solver, num_houses):
    """Robust clue parsing with multiple pattern matching."""
    clue_lower = clue.lower()
    is_negation = " not " in clue_lower or " doesn't " in clue_lower or " don't " in clue_lower

    # Find entities - get all occurrences
    sorted_vars = sorted(all_vars, key=len, reverse=True)
    entity_positions = []

    for v in sorted_vars:
        pattern = r'\b' + re.escape(v.lower()) + r'\b'
        for match in re.finditer(pattern, clue_lower):
            entity_positions.append((match.start(), v))

    # Remove duplicates
    seen = set()
    unique = []
    for pos, var in sorted(entity_positions):
        if var not in seen:
            seen.add(var)
            unique.append(var)

    ents = unique

    # Extract house numbers - very explicit patterns only
    nums = []
    explicit = [
        r'house\s+(?:number\s+)?(\d+)',
        r'in\s+(?:house\s+)?(\d+)',
        r'lives\s+in\s+(?:house\s+)?(\d+)',
        r'is\s+in\s+(?:house\s+)?(\d+)',
        r'numbered\s+(\d+)',
    ]

    for pattern in explicit:
        for m in re.finditer(pattern, clue_lower):
            n = int(m.group(1))
            if 1 <= n <= num_houses:
                nums.append(n)

    # Ordinal words
    ordinals = {
        'first': 1, 'leftmost': 1,
        'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        'last': num_houses, 'rightmost': num_houses,
    }

    for word, num in ordinals.items():
        if word in clue_lower and 1 <= num <= num_houses:
            nums.append(num)

    if 'middle' in clue_lower:
        if num_houses == 3:
            nums.append(2)
        elif num_houses == 5:
            nums.append(3)

    # Apply constraints
    if len(ents) == 1 and len(nums) >= 1:
        e, n = ents[0], nums[0]
        if is_negation:
            if n in solver.domains[e]:
                solver.domains[e].remove(n)
        else:
            solver.domains[e] = {n}
        return

    if len(ents) >= 2:
        e1, e2 = ents[0], ents[1]

        if "next to" in clue_lower or "adjacent" in clue_lower or "beside" in clue_lower:
            if not is_negation:
                solver.add_constraint("next", [e1, e2])
            return

        if "left of" in clue_lower:
            imm = "immediately" in clue_lower or "directly" in clue_lower
            if not is_negation:
                solver.add_constraint("left", [e1, e2], extra=imm)
            return

        if "right of" in clue_lower:
            imm = "immediately" in clue_lower or "directly" in clue_lower
            if not is_negation:
                solver.add_constraint("left", [e2, e1], extra=imm)
            return

        # Default: same or different house
        if is_negation:
            solver.add_constraint("neq", [e1, e2])
        else:
            solver.add_constraint("eq", [e1, e2])


def solve_puzzle(puzzle_text, puzzle_id):
    try:
        return parse_and_solve(puzzle_text, puzzle_id)
    except:
        return json.dumps({"header": ["House"], "rows": []}), 0