# Cadence evaluation results

## Dataset: synthetic (16 clips)

### judge
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.75 | 0.75 | 0.75 | 6/2/2 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/13/5 |
| sound_repetition | 0.40 | 0.67 | 0.50 | 6/9/3 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/1/0 |
| **overall** | 0.32 | 0.55 | 0.41 | 12/25/10 |

### baseline
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 1.00 | 0.62 | 0.77 | 5/0/3 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/18/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/0/9 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/16/0 |
| **overall** | 0.13 | 0.23 | 0.16 | 5/34/17 |

### plain
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 1.00 | 0.12 | 0.22 | 1/0/7 |
| filler | 0.00 | 0.00 | 0.00 | 0/1/0 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/0/5 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/11/9 |
| **overall** | 0.08 | 0.05 | 0.06 | 1/12/21 |

False alarms on 3 fluent clips: judge=4, baseline=4

### Failure cases
- `north_wind_Samantha_0.wav`: missed ['sound_repetition'], spurious []
- `north_wind_Samantha_1.wav`: missed [], spurious [('sound_repetition', 8.52)]
- `north_wind_Daniel_0.wav`: missed [], spurious [('prolongation', 9.74)]
- `north_wind_Daniel_1.wav`: missed ['prolongation'], spurious [('sound_repetition', 3.9), ('sound_repetition', 4.24)]

## Dataset: real (4 clips)

### judge
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.57 | 0.80 | 0.67 | 4/3/1 |
| prolongation | 0.12 | 0.50 | 0.20 | 1/7/1 |
| sound_repetition | 0.50 | 0.50 | 0.50 | 1/1/1 |
| word_repetition | 1.00 | 1.00 | 1.00 | 1/0/0 |
| **overall** | 0.39 | 0.70 | 0.50 | 7/11/3 |

### baseline
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.50 | 0.20 | 0.29 | 1/1/4 |
| filler | 0.00 | 0.00 | 0.00 | 0/2/0 |
| prolongation | 0.10 | 1.00 | 0.18 | 2/18/0 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/0/2 |
| word_repetition | 0.33 | 1.00 | 0.50 | 1/2/0 |
| **overall** | 0.15 | 0.40 | 0.22 | 4/23/6 |

### plain
| type | P | R | F1 | tp/fp/fn |
|---|---|---|---|---|
| block | 0.00 | 0.00 | 0.00 | 0/0/5 |
| prolongation | 0.00 | 0.00 | 0.00 | 0/0/2 |
| sound_repetition | 0.00 | 0.00 | 0.00 | 0/0/2 |
| word_repetition | 0.00 | 0.00 | 0.00 | 0/0/1 |
| **overall** | 0.00 | 0.00 | 0.00 | 0/0/10 |

False alarms on 2 fluent clips: judge=4, baseline=4

### Failure cases
- `rainbow_clean.wav`: missed [], spurious [('block', 2.38), ('prolongation', 13.02), ('prolongation', 15.9)]
- `northwind_clean.wav`: missed [], spurious [('block', 1.5)]
- `rainbow_stutter.wav`: missed [], spurious [('prolongation', 2.42), ('prolongation', 2.94), ('block', 8.44), ('prolongation', 10.14), ('prolongation', 21.0)]
- `northwind_stutter.wav`: missed ['prolongation', 'sound_repetition', 'block'], spurious [('prolongation', 4.5), ('sound_repetition', 7.8)]
