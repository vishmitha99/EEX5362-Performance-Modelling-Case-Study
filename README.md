💡 Traffic Flow Simulation – Case Study  🎯 Project Overview
This project simulates a four way traffic light system to study how different control methods affect city traffic.

The main goal is to compare a fixed time controller  which changes light at set times with  demand responsive controller which adjusts lights based on real traffic. 
The study looks at how well each system works under different traffic conditions.

The key performance metrics are:

Average Vehicle Delay
Average Queue Length

🧠 Key Metrics
During each simulation run, the system tracked critical performance measures:

Average Vehicle Delay (seconds)
Average Queue Length (vehicles)

These metrics were used to quantify the efficiency and congestion levels resulting from the different control policies.

📊 Results and Visualizations

Figure,Description
Figure 1,Comparative Average Vehicle Delay by Scenario
Figure 2,Comparative Average Queue Length by Scenario

💡 Insights & Recommendations

DRC Superiority:
The demand responsive controller surpasses the fixed time controller by matching service time to instantaneously demanded time. This prevents green waste and minimizes collective delay. 

Throughput vs. Policy: 
The simulation demonstrates that Throughput is largely limited by the physical clearance rate  and the aggregate arrival rate not the control policy. The control policy simply determines how long vehicles must wait.

Trade off: Switching Overhead: 
Frequent switching of the light e.g. green time too short is inefficient due to the 5second light change overhead. Minimum green time is required to balance this trade off.

✍️ Author

D.M.V.C.Dissanayaka
Final Year BSE (Hons) Student
The Open University of Sri Lanka
📧 s92085735@ousl.lk
