import sys
import subprocess

"""
    Max succ prob vs mu
"""
def vs_mu():
    mu_range = []
    success_prob_range = []
    
    for mu in range(10, 101, 10):
        # print(f"Running for tau = {mu}")
        mu_range.append(mu)
        # success_prob = run_simulation(max_execution_time = mu, epr_life = 15, gen_success_probability = 0.5, swap_succ_prob = 0.5, sim_gen_time = 0.002, model_gen_time = 5, model_swap_time = 10)
        success_prob = float(subprocess.check_output([sys.executable, "run_simulation.py", str(mu), "15", "0.5", "0.5", "0.002", "5", "10"]).decode())
        print(f'Success probability : {success_prob}')
        success_prob_range.append(success_prob)
    
    #Writing output to excel file
    write_xls(mu_range, success_prob_range,"mu")

    print(f'mu_range: {mu_range}')
    print(f'success_prob_range: {success_prob_range}')
    
"""
    Max succ prob vs t_bsm
"""
def vs_t_bsm():
    t_bsm_range = []
    success_prob_range = []
    
    for t_bsm in range(0, 51, 5):
        # print(f"Running for t_bsm = {t_bsm}")
        t_bsm_range.append(t_bsm)
        # success_prob = run_simulation(max_execution_time = 100, epr_life = 50, gen_success_probability = 0.5, swap_succ_prob = 0.5, sim_gen_time = 0.002, model_gen_time = 10, model_swap_time = t_bsm)
        success_prob = float(subprocess.check_output([sys.executable, "run_simulation.py", "100", "50" ,"0.5", "0.5", "0.002", "10", str(t_bsm)]).decode())
        print(f'Success probability : {success_prob}')
        success_prob_range.append(success_prob)
    
    #Writing output to excel file
    write_xls(t_bsm_range, success_prob_range,"tbsm")

    print(f't_bsm_range: {t_bsm_range}')
    print(f'success_prob_range: {success_prob_range}')
    
"""
    Max succ prob vs t_gen
"""
def vs_t_gen():
    t_gen_range = []
    success_prob_range = []
    
    for t_gen in range(0, 51, 5):
        if t_gen == 0 :
            t_gen = 0.0000001
        
        # print(f"Running for t_gen = {t_gen}")
        # success_prob = run_simulation(max_execution_time = 100, epr_life = 50, gen_success_probability = 0.5, swap_succ_prob = 0.5, sim_gen_time = 0.002, model_gen_time = t_gen, model_swap_time = 50)
        success_prob = float(subprocess.check_output([sys.executable, "run_simulation.py", "100", "50" ,"0.5", "0.5", "0.002", str(t_gen), "50"]).decode())
        print(f'Success probability : {success_prob}')
        success_prob_range.append(success_prob)
        
        if t_gen == 0.0000001:
            t_gen = 0

        t_gen_range.append(t_gen)
    
    #Writing output to excel file
    write_xls(t_gen_range, success_prob_range,"tgen")

    print(f't_gen_range: {t_gen_range}')
    print(f'success_prob_range: {success_prob_range}')
    
"""
    Max succ prob vs p_bsm
"""
def vs_p_bsm():
    p_bsm_range = []
    success_prob_range = []

    for p_bsm in range(0, 11, 1):
        # print(f"Running for p_bsm = {p_bsm/10}")
        p_bsm_range.append(p_bsm/10)
        # success_prob = run_simulation(max_execution_time = 50, epr_life = 15, gen_success_probability = 0.5, swap_succ_prob = p_bsm/10, sim_gen_time = 0.002, model_gen_time = 5, model_swap_time = 10)
        success_prob = float(subprocess.check_output([sys.executable, "run_simulation.py", "50", "15" ,"0.5", str(p_bsm/10), "0.002", "5", "10"]).decode())
        print(f'Success probability : {success_prob}')
        success_prob_range.append(success_prob)

    #Writing output to excel file
    write_xls(p_bsm_range, success_prob_range,"pbsm")

    print(f'p_bsm_range: {p_bsm_range}')
    print(f'success_prob_range: {success_prob_range}')
    
"""
    Max succ prob vs p_gen
"""
def vs_p_gen():
    p_gen_range = []
    success_prob_range = []

    for p_gen in range(0, 11, 1):
        # print(f"Running for p_bsm = {p_gen/10}")
        p_gen_range.append(p_gen/10)
        #success_prob = run_simulation(max_execution_time = 50, epr_life = 15, gen_success_probability = p_gen/10, swap_succ_prob = 0.5, sim_gen_time = 0.002, model_gen_time = 5, model_swap_time = 10)
        success_prob = float(subprocess.check_output([sys.executable, "run_simulation.py", "50", "15" ,str(p_gen/10), "0.5", "0.002", "5", "10"]).decode())
        print(f'Success probability : {success_prob}')
        success_prob_range.append(success_prob)
    
    #Writing output to excel file
    write_xls(p_gen_range, success_prob_range,"pgen")

    print(f'p_gen_range: {p_gen_range}')
    print(f'success_prob_range: {success_prob_range}')

"""
    Max succ prob vs tau
"""
def vs_tau():
    tau_range = []
    success_prob_range = []
    
    for tau in range(0, 51, 5):
        if tau == 0 :
            tau = 0.0000001

        # success_prob = run_simulation(max_execution_time = 50, epr_life = tau, gen_success_probability = 0.5, swap_succ_prob = 0.5, sim_gen_time = 0.002, model_gen_time = 5, model_swap_time = 10)
        success_prob = float(subprocess.check_output([sys.executable, "run_simulation.py", "50", str(tau) ,"0.5", "0.5", "0.002", "5", "10"]).decode())
        print(f'Success probability : {success_prob}')
        success_prob_range.append(success_prob)

        if tau == 0.0000001:
            tau = 0
        
        tau_range.append(tau)

    #Writing output to excel file
    write_xls(tau_range, success_prob_range,"tau")

    print(f'tau_range: {tau_range}')
    print(f'success_prob_range: {success_prob_range}')

#To write simulator's data to an output file
def write_xls(x_vals, succ_probs, choice):
    header = choice+',result\n'
    with open("../../results/simulator-"+choice+".csv",'w') as fout:
        fout.write(header)
        for i in range(len(x_vals)):
            fout.write(str(x_vals[i])+","+str(succ_probs[i]))
            if i != len(x_vals)-1:
                fout.write("\n")     


if __name__ == "__main__":
    if len(sys.argv) == 1:
        vs_tau()
        vs_p_gen()
        vs_p_bsm()
        vs_t_gen()
        vs_t_bsm()
        vs_mu()
    else:
        choice = sys.argv[1]
        if choice == "tau":
            vs_tau()
        elif choice == "pgen":
            vs_p_gen()
        elif choice == "pbsm":
            vs_p_bsm()
        elif choice == "tgen":
            vs_t_gen()
        elif choice == "tbsm":
            vs_t_bsm()
        elif choice == "mu":
            vs_mu()

