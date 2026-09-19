# Cadence evaluation results

## Dataset: synthetic (16 clips)

### judge
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.86 | 0.75 | 0.80 | 6/1/2 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/15/5 |
| sound_repetition | 0.50 | 0.22 | 0.31 | 2/2/7 |
| **overall** | 0.31 | 0.36 | 0.33 | 8/18/14 |

### baseline
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 1.00 | 0.50 | 0.67 | 4/0/4 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/20/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/0/9 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/4/0 |
| **overall** | 0.14 | 0.18 | 0.16 | 4/24/18 |

### plain
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.00 | 0.00 | 0.00 | 0/0/8 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/0/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/4/9 |
| **overall** | 0.00 | 0.00 | 0.00 | 0/4/22 |

False alarms on 3 fluent clips: judge=4, baseline=4

### Failure cases
- `north_wind_Samantha_0.wav`: missed ['sound_repetition'], spurious []
- `north_wind_Samantha_1.wav`: missed ['sound_repetition'], spurious []
- `north_wind_Daniel_0.wav`: missed [], spurious [('prolongation', 9.74)]
- `north_wind_Daniel_1.wav`: missed ['prolongation'], spurious []

## Dataset: real (4 clips)

### judge
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.44 | 1.00 | 0.62 | 4/5/0 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/7/1 |
| word_repetition | 1.00 | 1.00 | 1.00 | 1/0/0 |
| **overall** | 0.29 | 0.83 | 0.43 | 5/12/1 |

### baseline
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.50 | 0.25 | 0.33 | 1/1/3 |
| filler | 0.00 | 0.00 | 0.00 | 0/2/0 |
| prolongation | 0.05 | 1.00 | 0.10 | 1/19/0 |
| word_repetition | 1.00 | 1.00 | 1.00 | 1/0/0 |
| **overall** | 0.12 | 0.50 | 0.19 | 3/22/3 |

### plain
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.00 | 0.00 | 0.00 | 0/0/4 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/0/1 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/4/1 |
| **overall** | 0.00 | 0.00 | 0.00 | 0/4/6 |

False alarms on 2 fluent clips: judge=3, baseline=4

### Failure cases
- `rainbow_clean.wav`: missed [], spurious [('block', 2.38), ('prolongation', 13.02), ('prolongation', 15.9)]
- `rainbow_stutter.wav`: missed [], spurious [('prolongation', 2.42), ('prolongation', 2.94), ('block', 8.44), ('prolongation', 10.08), ('prolongation', 21.0)]
- `northwind_stutter.wav`: missed ['prolongation'], spurious [('block', 6.0), ('prolongation', 11.96), ('block', 18.06), ('block', 25.12)]
