import numpy as np

if __name__ == "__main__":
    
    a = [[2.2763421535491943, -0.766880989074707, 0.15159186720848083, 5],
 [5.838303565979004, 1.6567497253417969, 0.41085585951805115, 3],
 [6.053800582885742, 1.870169997215271, 0.7068805694580078, 3],
 [6.276348114013672, 1.5868682861328125, 0.4764494001865387, 3],
 [6.476734638214111, 0.34534314274787903, 0.4096130132675171, 3],
 [9.16502857208252, -1.4294748306274414, -0.06541356444358826, 9],
 [9.15156364440918, -1.4871002435684204, 0.14209459722042084, 9],
 [9.484023094177246, -1.4838229417800903, 0.5026817917823792, 9]]
    b= "/home/mboghl21studentaaudk/tiago_public_ws/centroids.npy"
    np.save(b, a)
    print("done")
    
    