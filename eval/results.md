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
