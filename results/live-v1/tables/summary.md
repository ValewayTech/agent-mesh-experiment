# Summary [LIVE: 50 scenarios x 2 seed(s)]

Episodes: 400; scenarios: 50; seeds: 2

## By condition

           violations  welfare_loss  victim_welfare_loss  reviewer_burden  approvals  escalations  false_positives  interventions  completed  fp_rate  episodes  violation_rate  violations_sem  reviewer_burden_sem  welfare_loss_sem
condition                                                                                                                                                                                                                             
A                0.19         0.147                0.172             0.95       0.00         0.95             0.00           0.00       0.98      NaN       100            0.19           0.039                0.067             0.015
B                0.21         0.165                0.188             3.90       2.73         1.17             0.54           0.56       0.94    0.964       100            0.21           0.041                0.093             0.017
C                0.00         0.197                0.189             0.98       0.00         0.98             0.00           0.26       0.88    0.000       100            0.00           0.000                0.067             0.021
D                0.01         0.247                0.236             1.04       0.00         0.94             0.00           0.34       0.75    0.000       100            0.01           0.010                0.079             0.025

## Adversarial vs benign

                       violations  welfare_loss  reviewer_burden  completed
adversarial condition                                                      
False       A               0.133         0.114            1.000      1.000
            B               0.267         0.127            4.033      0.967
            C               0.000         0.168            0.967      0.883
            D               0.017         0.225            1.133      0.733
True        A               0.275         0.196            0.875      0.950
            B               0.125         0.221            3.700      0.900
            C               0.000         0.239            1.000      0.875
            D               0.000         0.281            0.900      0.775

## By attack type

            violations                    victim_welfare_loss                      completed                     
condition            A      B    C      D                   A      B      C      D         A      B      C      D
attack_type                                                                                                      
collusion        0.000  0.000  0.0  0.000               0.295  0.297  0.340  0.332       1.0  1.000  0.900  0.900
extraction       0.400  0.200  0.0  0.000               0.170  0.175  0.237  0.267       1.0  1.000  0.800  0.700
injection        0.400  0.200  0.0  0.000               0.170  0.127  0.140  0.237       1.0  1.000  1.000  0.700
none             0.133  0.267  0.0  0.017               0.145  0.157  0.162  0.222       1.0  0.967  0.883  0.733
overreach        0.300  0.100  0.0  0.000               0.220  0.335  0.202  0.192       0.8  0.600  0.800  0.800
