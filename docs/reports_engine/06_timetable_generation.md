# 06. Automatic Timetable Generation Algorithm

The Timetable Generation engine (`timetable_mgmt.py`) uses a randomized greedy algorithmic approach to plot subjects across a multidimensional matrix (Days $\times$ Periods) while enforcing distribution constraints to prevent subject clustering.

---

## 1. Matrix and Variable Definitions

Before generation, the algorithm defines the boundaries of the scheduling matrix based on user-defined parameters or defaults.

*   $D$ = Number of operational days per week (e.g., 5 days)
*   $P$ = Number of slots per day (e.g., 8 periods)
*   $T = D \times P$ (Total number of available slots in the weekly matrix)
*   $S = \{s_1, s_2, ..., s_k\}$ (Set of all subjects assigned to a specific course and semester)
*   $L_{s_i}$ = The legally required minimum weekly lectures for subject $s_i \in S$

The empty timetable schedule is represented as a 2-Dimensional Matrix where every coordinate $(d, p)$ is initially set to $Null$.

---

## 2. Stochastic Pool Construction

The algorithm first generates a flat array (the "Pool") containing all the lectures perfectly required for the week.

### Step 2.1: Minimum Requirements
For every subject $s \in S$, the subject is appended to the $Pool$ exactly $L_s$ times.
```math
Pool = \{ \underbrace{s_1, ..., s_1}_{L_{s_1} \text{ times}}, \underbrace{s_2, ..., s_2}_{L_{s_2} \text{ times}}, ... \}
```

### Step 2.2: Matrix Padding (Gap Filling)
In many academic cases, the sum of required weekly lectures $\sum_{i=1}^{k} L_{s_i}$ is less than the total available slots $T$. Leaving slots empty is inefficient.
If $|Pool| < T$, the system recursively adds available subjects into the pool in a round-robin format until the pool perfectly fits the matrix:
```math
\text{While } |Pool| < T \text{ do:} 
\implies Pool \leftarrow Pool \cup \{s_i\}
```

### Step 2.3: Randomization
To ensure the generated timetable doesn't artificially prioritize subjects placed earlier in the array, the entire $Pool$ is randomly shuffled via a stochastic jump function, resulting in a randomized queue $Q$.

---

## 3. The Spread Constraints (Daily Limits)

To prevent a student from studying the exact same subject for 4 periods in a row on a single day, the engine calculates a hard upper bound Limit ($MAX_s$) for every subject per day.

Let $C_s$ be the absolute total frequency of subject $s$ in the finalized randomized queue $Q$.
```math
MAX_s = \lceil \frac{C_s}{D} \rceil
```
*Example: If Database Management appears 6 times in the queue, and there are 5 Days, the limit is $\lceil 6 / 5 \rceil = 2$. Database Management can never be scheduled more than 2 times on the same day.*

---

## 4. Greedy Placement Pipeline

The scheduling engine uses a first-fit greedy algorithm with constraint checking to empty the queue $Q$ into the $Schedule$ matrix $M(d, p)$.

For every single item $x$ extracted from $Queue$:

**Iterate through Days ($d = 1$ to $D$):**
1. **Constraint Check:** Count the current occurrences of $x$ in row $d$.
   If $Count(x, d) \ge MAX_x$, the day constraint is violated. The engine aborts day $d$ and skips to day $d+1$.
2. **First-Fit Placement:** Iterate through periods ($p = 1$ to $P$).
   *   If $M(d, p) == Null$:
       *   Assign $M(d, p) = x$
       *   Mark $x$ as successfully scheduled.
       *   Break operation and move to the next item in the Queue.

### Resolution of Deadlocks

Because it is a greedy first-fit algorithm, the final items in the $Queue$ may experience a "deadlock" where all remaining $Null$ slots occur on days where the subject has already hit its $MAX_x$ limit.

If an item $x$ loops through all $D$ days and fails the constraint check on every available day, it cannot be safely placed. The engine ejects the lecture and appends it to an `Unplaced` array, flagging a non-blocking warning to the administrator that the timetable constraints may be too tight for the given matrix size.
