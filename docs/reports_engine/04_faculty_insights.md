# 04. Faculty Archetypes

Faculty evaluation isn't just based on pass rates; it leverages mathematical equity tracking to classify teaching styles.

## 1. Performance Index (Class Average)
The standard metric. The average marks obtained by all students taking the specific subject taught by the faculty member.
```math
\text{Performance}_{\mu} = \text{Mean(Student Scores)}
```

## 2. Equity Score
Measures "inclusive teaching." A high equity score means the entire class understands the material equally. A low equity score means there's a huge divide between top students and failing students.
```math
\text{Equity Score} = \max\left(0, 100 - (StandardDeviation \times 2.0)\right)
```
*   **Why times 2.0?** A standard deviation of exactly 20 is heavily penalized ($100 - 40 = 60$ Equity). If the teacher ensures tight groupings ($\sigma < 10$), their equity score stays firmly above 80.

## 3. Pedagogical Classification Matrix

Faculty are slotted into one of four archetypes based on the resulting $(X, Y)$ coordinates of Performance and Equity.

| Archetype | Performance ($\mu$) | Equity Score | Color Flag | Description |
| :--- | :--- | :--- | :--- | :--- |
| **The Master Teacher** | $\ge$ 60 | $\ge$ 60 | Emerald | High Scores, High Equity. The ideal outcome. |
| **The Elite Coach** | $\ge$ 65 | $<$ 60 | Indigo | High Scores, Low Equity. Focuses heavily on top-tier students. |
| **The Empathetic Guide** | $<$ 55 | $\ge$ 65 | Blue | Low Scores, High Equity. The whole class struggles equally; exam might be too hard. |
| **The Strict Evaluator** | $<$ 65 | $<$ 45 | Red | Low Equity (Chaos). Significant divide in class understanding. |
