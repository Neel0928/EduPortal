# 02. Student Performance & Velocity

The Student Performance intelligence module maps academic DNA and calculates growth velocity curves.

## 1. Growth Velocity
Measures improvement or decay between Semester 1 and Semester 3.
1. Map average scores for Sem 1 ($Avg_{s1}$) and Sem 3 ($Avg_{s3}$).
2. The formula calculates relative percentage growth:
```math
Growth = \left( \frac{Avg_{s3} - Avg_{s1}}{Avg_{s1}} \right) \times 100
```
*   **Improving:** Batch average growth > +2%
*   **Stable:** Batch average growth between -2% and +2%
*   **Declining:** Batch average growth < -2%

## 2. Consistency Matrix (Scatter Plot)
Evaluates a student's performance stability.
*   **X-Axis (Performance):** Mean of all marks ($\mu$)
*   **Y-Axis (Volatility):** Standard Deviation of all marks ($\sigma$)
```math
\sigma = \sqrt{ \frac{1}{N-1} \sum_{i=1}^{N} (x_i - \mu)^2 }
```
A highly consistent student has a very low standard deviation (Y-axis), forming a tight cluster on the scatter plot. A student who scores 90 in one subject and 30 in another has high volatility.

## 3. Academic DNA (Radar Chart)
Averaged performance across major subject buckets.
To prevent UI clutter, the system dynamically queries the **Top 7 Subjects** (based on total number of exam results) and plots the `Global Average` for each of those 7 subjects. This shows the institutional strengths and weaknesses by discipline.
