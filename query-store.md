* Are a-c entangled when simulation finishes

P_ac() = if (s.rval(3) == 1.0) then s.rval(4) else # P_ac() fi ;
eval E[ P_ac() ] ;

-> [New Logic]
P_ac() = if (s.rval(3) == 1.0) then s.rval("Entangled: (a, c)") else # P_ac() fi ;
eval E[ P_ac() ] ;

* Given a time limit, are a-c entangled when that time limit is reached?

P_ac() = if (s.rval(0) > TIME_LIMIT) then s.rval(4) else # P_ac() fi;
eval E[ P_ac() ];

P_ac() = if (s.rval(0) > 1.5) then s.rval(4) else # P_ac() fi;
eval E[ P_ac() ];

-> [New Logic]
P_ac() = if (s.rval(0) > 1.5) then s.rval("Entangled: (a, c)") else # P_ac() fi;
eval E[ P_ac() ];

Slightly different logic for same thing:
P_ac() = if (s.rval(0) < 1.5) then if(s.rval("Entangled: (a, c)") == 1) then 1 else # P_ac() fi else 0 fi;
eval E[ P_ac() ];

P_ac() = if (s.rval(0) > 3) then s.rval("Entangled: (a, c)") else # P_ac() fi;
eval E[ P_ac() ];


* If one side is entangled at timestep t, is the swap completed within t+delta?
P_swap(T) = if(s.rval(0)>T) 
                then 0 
            else if((s.rval("Entangled: (a, b)") == 1) && (s.rval("Entangled: (b, c)") == 1))
                then 1 
                else if((s.rval("Entangled: (a, b)") == 1) || (s.rval("Entangled: (b, c)") == 1)) 
                    then 
                        #P_swap(s.rval(0)+0.0000001)
                    else
                        #P_swap(T) 
                    fi
                fi 
            fi;
eval E[ P_swap(1000) ];

P_swap(T) = if(s.rval(0)>T) 
                then 0 
            else if((s.rval("Entangled: (a, b)") == 1) && (s.rval("Entangled: (b, c)") == 1))
                then 1 
                else if((s.rval("Entangled: (a, b)") == 1) || (s.rval("Entangled: (b, c)") == 1)) 
                    then 
                        #P_swap(s.rval(0)+0.0000001)
                    else
                        #P_swap(T) 
                    fi
                fi 
            fi;
eval E[ P_swap(1000) ];

* If all memories have lifetimes greater than LIFE_TIME, the probability of final entanglement being distributed within a timebound

P_e2e(T) = if(s.rval("MEM_LIFETIME: 1") == 1)
            then if(s.rval(0) < T)
                    then if(s.rval("Entangled: (a, b)") == 1)
                                then 1
                        else #P_e2e(T)
                        fi
                else 0 
                fi
            else 1
            fi;
eval E[ P_e2e(1.004) ];

* P_ac(T) = if (s.rval(0) > T) then s.rval("Entangled: (a, d)") else  # P_ac(T) fi;
eval parametric(E[ P_ac(T) ], T, 1, 0.009, 1.049002000110);

* P_ac() = if (s.rval(0) > 1.049002000110) then s.rval("Entangled: (a, e)") else  # P_ac() fi;
eval E[ P_ac() ];
        |
    rewritten
        |

* vs tau:
  P_ac() = if (s.rval(0) > 1.049002000110) 
            then s.rval("Entangled: (a, c)") 
         else  
            #P_ac()
         fi;
eval E[ P_ac() ];

  with swap fail limited to 1:
  P_ac() = if (s.rval(0) > 1.049002000110) 
            then s.rval("Entangled: (a, c)") 
         else if (s.rval("SWAP_FAILED: 1") == 1) 
                then 0 
              else  
                #P_ac() 
              fi 
         fi;
    eval E[ P_ac() ];

    ----FINAL AND CORRECT (VS TAU) ----
    P_ac() = if (s.rval(0) > 1.02) 
            then s.rval("Entangled: (a, c)") 
          else if (s.rval("SWAP_FAILED: 1") == 1) 
                then 0 
              else  
                #P_ac() 
              fi 
          fi;
    eval E[ P_ac() ];


    Corrected for early entanglement detection:

    P_ac() = if (s.rval(0) > 1.02 || s.rval("Entangled: (a, c)") == 1) 
            then s.rval("Entangled: (a, c)") 
          else if (s.rval("SWAP_FAILED: 1") == 1) 
                then 0 
              else  
                #P_ac() 
              fi 
          fi;
    eval E[ P_ac() ];

* vs mu(total time):
    P_ad(T) = if (s.rval(0) > T*0.00001)
                then s.rval("Entangled: (a, d)") 
              else  
                # P_ac(T) 
              fi;
    eval parametric(E[ P_ad(T) ], T, 100000, 5, 101500);

    P_ad(T) = if (s.rval(0) > T*0.00001) 
                then s.rval("Entangled: (a, c)") 
          else if (s.rval("SWAP_FAILED: 1") == 1) 
                then 0 
              else  
                #P_ad(T) 
              fi 
         fi;
    eval parametric(E[ P_ad(T) ], T, 100000, 5, 101500);

    ----FINAL AND CORRECT (VS MU) ----
    {"LIFE_TIME": ".006"}
    
    P_ac(T) = if (s.rval(0) > T*0.001) 
                then s.rval("Entangled: (a, c)") 
          else if (s.rval("SWAP_FAILED: 1") == 1) 
                then 0 
              else  
                #P_ac(T) 
              fi 
         fi;
    eval parametric(E[ P_ac(T) ], T, 1000, 1, 1030);

    Correcting for early entanglement check

    P_ac(T) = if (s.rval(0) > T*0.001 || s.rval("Entangled: (a, c)") == 1) 
                then s.rval("Entangled: (a, c)") 
          else if (s.rval("SWAP_FAILED: 1") == 1) 
                then 0 
              else  
                #P_ac(T) 
              fi 
         fi;
    eval parametric(E[ P_ac(T) ], T, 1004, 4, 1041);

java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 1000 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/vs_mu/1000-1004_1040.txt"

* vs retrial attempts:

  1. Keeping good links fixed at 10 retrials and varying bad from 1 to 30 retrials

  P_ae(ab, bc, cd, de) = 
          if (s.rval(0) > 1.1 || s.rval("Entangled: (a, e)") == 1) 
            then s.rval("Entangled: (a, e)") 
          else if (s.rval("RETRIALS: (a, b)") <= ab && 
                    s.rval("RETRIALS: (b, c)") <= bc && 
                    s.rval("RETRIALS: (c, d)") <= cd && 
                    s.rval("RETRIALS: (d, e)") <= de)
                  then #P_ae(ab, bc, cd, de) 
                else
                  0
                fi
          fi;
  eval parametric(E[ P_ae(10, 10, retrials, retrials) ], retrials, 1, 1, 30);

  Command:
java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 1000 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/retrials/good-fixed-runs-1000.txt"

  2. Keeping bad links fixed at 10 retrials and varying good from 1 to 30 retrials

  P_ae(ab, bc, cd, de) = 
          if (s.rval(0) > 1.1 || s.rval("Entangled: (a, e)") == 1) 
            then s.rval("Entangled: (a, e)") 
          else if (s.rval("RETRIALS: (a, b)") <= ab && 
                    s.rval("RETRIALS: (b, c)") <= bc && 
                    s.rval("RETRIALS: (c, d)") <= cd && 
                    s.rval("RETRIALS: (d, e)") <= de)
                  then #P_ae(ab, bc, cd, de) 
                else
                  0
                fi
          fi;
  eval parametric(E[ P_ae(retrials, retrials, 10, 10) ], retrials, 1, 1, 30);

  command:
java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 1000 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/retrials/bad-fixed-runs-1000.txt"

* Diff schedule comparison while keeping bad links fixed

java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 1000 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/retrials/diff-schedule-bad-fixed-runs-1000.txt"

* schedule comparison changing memory params to 0.010 for all

P_ae(ab, bc, cd, de) = 
          if (s.rval(0) > 1.1 || s.rval("Entangled: (a, e)") == 1) 
            then s.rval("Entangled: (a, e)") 
          else if (s.rval("RETRIALS: (a, b)") <= ab && 
                    s.rval("RETRIALS: (b, c)") <= bc && 
                    s.rval("RETRIALS: (c, d)") <= cd && 
                    s.rval("RETRIALS: (d, e)") <= de)
                  then #P_ae(ab, bc, cd, de) 
                else
                  0
                fi
          fi;
  eval parametric(E[ P_ae(retrials, retrials, retrials, retrials) ], retrials, 1, 1, 30);


* vs delta for swap:

3 nodes -

P_swap(T, delta) = if(s.rval(0)>T) 
                then 0 
            else if((s.rval("Entangled: (a, b)") == 1) && (s.rval("Entangled: (b, c)") == 1))
                then 1 
                else if(((s.rval("Entangled: (a, b)") == 1) || (s.rval("Entangled: (b, c)") == 1)) && (T == 1000)) 
                    then
                        #P_swap(s.rval(0)+delta*0.0001, delta)
                    else
                        #P_swap(T, delta) 
                    fi
                fi 
            fi;
eval parametric(E[ P_swap(1000, delta) ], delta, 0, 5, 120);


java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 1000 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/delta/3-nodes-1000runs.txt

4 nodes-

(NEEDS TO BE CORRECTED)

P_swap(TswapB, TswapC, delta) = 
if(s.rval(0)>TswapC) 
    then 0 
else if((s.rval("Entangled: (a, c)") == 1) && (s.rval("Entangled: (c,d)") == 1))
        then 1 
    else if(s.rval("Entangled: (c, d)") == 1) 
            then if((s.rval(0) > TswapB) && !((s.rval("Entangled: (a, b)") == 1) && (s.rval("Entangled: (b,c)") == 1)))
                    return 0
                    else if ((s.rval("Entangled: (a, c)") == 1) || (s.rval("Entangled: (c,d)") == 1) && (TswapB != 1000))
                        then if(TswapC == 1000)
                                then #P_swap(s.rval(0)+delta, s.rval(0)+delta, delta)
                            else
                                #P_swap(s.rval(0)+delta, TswapC, delta) 
                        else if(TswapC == 1000)
                                then #P_swap(TswapB, s.rval(0)+delta, delta)
                            else
                                #P_swap(TswapB, TswapC, delta)
        else
            if(TswapC == 1000)
                then #P_swap(TswapB, s.rval(0)+delta, delta)
            else
                #P_swap(TswapB, TswapC, delta)
        fi
    fi 
fi;
eval E[ P_swap(1.01) ];




----Execution commands-----

Running within bash script
java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 2 -sots 1 -sd vesta.python.simpy.SimPyState -vp true -bs 1 -ds '[10]' -a 0.05 -otherParams "python3" > "op_tau$tau.txt"

Running Python Script
java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 2 -sots 1 -sd vesta.python.simpy.SimPyState -vp true -bs 10 -ds '[10]' -a 0.05 -otherParams "python3"
