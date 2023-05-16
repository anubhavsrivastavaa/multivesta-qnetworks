for tau in `seq 1 2 20`
do
    echo $tau
    tau=$(bc <<< "scale=3; $tau/1000")
    python3 update_config.py $tau
    java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 1000 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/vs_tau/tau_1000_swap_limit_1to20_before_1_02.txt"
done

#vs mu(total time)
# java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f query.multiquatex -l 4 -sots 1 -sd vesta.python.simpy.SimPyState -vp false -bs 500 -ds '[10]' -a 0.05 -otherParams "python3" >> "results/vs_mu/mu_500_swap_limit_10to30.txt"



