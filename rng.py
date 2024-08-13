#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

def generate_lognormal_numbers(mean=50, size=100, lower_bound=10, upper_bound=1000):
    # Calculate the shape and scale parameters for the log-normal distribution
    mu = np.log(mean)
    sigma = (np.log(upper_bound) - np.log(lower_bound)) / 2
    
    # Generate log-normal distributed numbers
    samples = np.random.lognormal(mean=mu, sigma=sigma, size=size)
    
    # Clip the results to lie within a specific range
    if False:
        clipped_samples = np.clip(samples, 0.0001, 1e6)
    else:
        clipped_samples = samples

    return clipped_samples

def approximate_mean():
    return 710.0


def main():
    # Example usage:
    numbers = generate_lognormal_numbers(size=1_000_000)

    # Plotting the distribution using a histogram and KDE
    plt.figure(figsize=(8, 5))

    # Histogram
    import seaborn as sns
    sns.histplot(numbers, bins=50, kde=False, color='blue', alpha=0.6, label='Swaps')

    # KDE (Kernel Density Estimate)
    #sns.kdeplot(numbers, color='red', label='KDE')

    # Labels and title
    plt.xlabel('Value')
    plt.ylabel('Density')
    plt.legend()
    plt.yscale("symlog")

    # Show the plot
    plt.show()


if __name__ == '__main__':
    main()
    print("all done!")
