# 03. Attendance & Fatigue Analytics

This module analyzes non-academic engagement metrics, focusing on classroom fatigue and truancy.

## 1. Weekly Fatigue Index
Calculates institutional energy drops based on the day of the week.
1. Iterate over all `Attendance` records.
2. Extract the `weekday()` (0 = Monday, 4 = Friday).
3. For each weekday $d$:
```math
Rate_d = \left( \frac{PresentDays_d}{TotalDays_d} \right) \times 100
``` \
**AI Insight Generation:**
If the minimum rate across all 5 days drops below **70%**, the AI flags that day as a "Burnout Day" (Fatigue Detected) and recommends lighter activities.

## 2. Truancy Risk Prediction
Identifies students at risk of detachment or dropout based on attendance thresholds.
1. Group attendance by `student_id`.
2. Calculate individual attendance percentage.
```math
Attendance \% = \left( \frac{Present Days}{Total Recorded Days} \right) \times 100
```
3. If $Attendance \% < 75\%$, the student is flagged for Truancy Risk.
4. **Dropout Probability** is calculated algorithmically as the inverse of attendance:
```math
Probability_{dropout} = 100 - Attendance \%
```
*Note: This is a simplified linear model. If attendance drops to 40%, the probability of detachment/failure is rated at 60%.*
