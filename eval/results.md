# Cadence evaluation results

## Dataset: synthetic (16 clips)

### judge
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.80 | 0.50 | 0.62 | 4/1/4 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/15/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/0/9 |
| **overall** | 0.20 | 0.18 | 0.19 | 4/16/18 |

### baseline
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 1.00 | 0.50 | 0.67 | 4/0/4 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/20/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/0/9 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/7/0 |
| **overall** | 0.13 | 0.18 | 0.15 | 4/27/18 |

### plain
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.00 | 0.00 | 0.00 | 0/0/8 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/0/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/3/9 |
| **overall** | 0.00 | 0.00 | 0.00 | 0/3/22 |

False alarms on 3 fluent clips: judge=4, baseline=4

### Failure cases
- `north_wind_Samantha_0.wav`: missed ['sound_repetition'], spurious []
- `north_wind_Samantha_1.wav`: missed ['sound_repetition'], spurious []
- `north_wind_Daniel_0.wav`: missed [], spurious [('prolongation', 9.74)]
- `north_wind_Daniel_1.wav`: missed ['prolongation', 'block'], spurious []

## Dataset: real (4 clips)

### judge
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.44 | 1.00 | 0.62 | 4/5/0 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/11/1 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/0/1 |
| **overall** | 0.20 | 0.67 | 0.31 | 4/16/2 |

### baseline
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.50 | 0.25 | 0.33 | 1/1/3 |
| filler | 0.00 | 0.00 | 0.00 | 0/2/0 |
| prolongation | 0.04 | 1.00 | 0.08 | 1/22/0 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/0/1 |
| **overall** | 0.07 | 0.33 | 0.12 | 2/25/4 |

### plain
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.00 | 0.00 | 0.00 | 0/0/4 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/0/1 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/1/1 |
| **overall** | 0.00 | 0.00 | 0.00 | 0/1/6 |

False alarms on 2 fluent clips: judge=3, baseline=4

### Failure cases
- `rainbow_clean.wav`: missed [], spurious [('block', 2.38), ('prolongation', 13.02), ('prolongation', 15.9)]
- `rainbow_stutter.wav`: missed [], spurious [('prolongation', 2.42), ('prolongation', 2.94), ('block', 8.44), ('prolongation', 10.08), ('prolongation', 21.0)]
- `northwind_stutter.wav`: missed ['word_repetition', 'prolongation'], spurious [('prolongation', 2.56), ('prolongation', 3.26), ('prolongation', 3.88), ('block', 6.0), ('prolongation', 11.96), ('block', 18.06), ('prolongation', 23.54), ('block', 25.12)]
