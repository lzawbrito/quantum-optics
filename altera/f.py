import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()

arr = np.array([[604, 548, 650, 508, 467, 566, 363, 564]])

ax.plot([1,], arr)
plt.show()