The following two steps are used to set up the tuning process. 


1. Setting up the application and its search space:

Use the "application_setup.py" file for this purpose. In the "get_search_space()" function, define the search space of your application, i.e., the name of the parameters and the values that they can take. Currently, the "get_search_space()" function shows the search space defining format (in form of a dictionary) for a dummy application. 

The "execute_application()" function in "application_setup.py" is used to control function execution with the set parameters, passed to the function as "parameter_values". The "main.py" controls the passing of these parameters. Replace the two lines in the function, marked by "#replace with application invocation/execution command" comment, with the commands to execute your application with the passed parameter to the function ("parameter_values"). Currently, these two lines contain dummy execution commands. 


2. Running the DarwinGame tuner: 

Run the "main.py" file. It connects with the "application_setup.py" file to execute application with different chosen parameter configurations in the tuning process. Place both of these python files, along with the application you are tuning in a noisy/interference-prone environment to perform the tuning. The DarwinGame tuner in the "main.py" file contains the following knobs that can be configured based on your use-case. 

    # ---------------- Configurable knobs of the regional phase (inside the "main_regional_phase()" function) ----------------
    num_regions = 100               # How many total regions
    max_parallel_regions = 2        # How many regions can run concurrently in parallel
    players_per_game = 4            # How many configurations are co-located in each game
    max_rounds_in_region = 5        # Maximum number of rounds for each region
    top_percentage = 20.0           # Top performers are chosen as winners if average execution time <= (best execution time)*(1 + top_percentage/100)
    # ------------------------------------------------------------------------------- 
  

    # ----------------- Configurable knobs of the global phase (inside the "main_global_phase()" function) ----------------
    group_size = 8               # how many players per group in main bracket
    max_parallel_groups = 2      # how many groups can run in parallel
    top_percentage = 20.0        # top X% (by combined score) advance each round
    narrow_fraction = 0.10       # when the number of remaining players in main bracket <= 10% of initial number of players in main bracket, do a final single match
    max_global_rounds = 5        # maximum number of main bracket rounds allowed
    # ------------------------------------------------------------------------------- 

