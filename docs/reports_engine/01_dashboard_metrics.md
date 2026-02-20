# 01. Dashboard Global Metrics

The Executive Command Deck (`/reports`) serves as the high-level pulse check for the institution.

## 1. Academic Health (Global Batch Average)
Calculated by flattening all recorded `StudentResult` entities across the entire institution.
```math
Global Average = \frac{\sum_{i=1}^{N} \text{marks\_obtained}_i}{N}
```
*Where N is the total number of non-null exam result records.*

## 2. Critical Alerts (Danger Zone Count)
An alert is generated when a student's aggregate average across all subjects falls below the threshold of 40%.
1. Group all marks by `student_id`.
2. For each student, calculate `mean(marks)`.
3. If `mean(marks) < 40`, increment `danger_alerts`.

## 3. Top Performer & Projected Alpha Package
The highest projected salary package (LPA - Lakhs Per Annum) is tied directly to the student with the highest aggregate academic average. It uses the exact same deterministic formula employed by the Future Sight simulator (see Module 05).

**Variables:**
* $S_{\mu}$ = Student's mean score across all subjects
* $S_{\sigma}$ = Student's standard deviation (score consistency)

**Base Tier Logic:**
* If $S_{\mu} > 85$:
  * If $S_{\sigma} < 5$ (Highly consistent): Base = 12.0 LPA (Predicts Research/Academia path)
  * If $S_{\sigma} \ge 5$ (Spiky genius): Base = 18.0 LPA (Predicts niche highly-paid roles like Data Science)
* If $S_{\mu} > 70$: Base = 8.5 LPA
* If $S_{\mu} > 60$: Base = 6.5 LPA
* Else: Base = 4.5 LPA

**Variance Modifier:**
```math
Projected Package = Base + (S_{\sigma} \times 0.1)
```
The highest theoretical package generated from this loop becomes the "Projected Alpha" on the dashboard.
