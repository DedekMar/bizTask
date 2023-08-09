def count_pairs(arr):
    n = len(arr)
    count = 0
    # Since the array is ordered, if the first element of the entire array satisfies it, all of the subsequent ones will as well, we can return results straight away
    if arr[0] * arr[0] >= arr[0] + arr[0]:
            return n * n

    for i in range(n):
        # check if the current i element satisfies the condition with the first element in the array, if it does, it will always satisfy it and we can count n
        if arr[i] * arr[0] >= arr[i] + arr[0]:
            count += n
        l = 0
        r = n - 1

        # Do a binary search where the condition is checked, as well as that the condition of the previous element doesnt hold. 
        # I.e. find the first element, that satisfies the condition, all subsequent ones will as well
        while l <= r:
            mid = l + (r - l) // 2
            if arr[i] * arr[mid] >= arr[i] + arr[mid] and (arr[i] * arr[mid-1] < arr[i] + arr[mid-1]):
                count += n - mid
                break
            
            elif arr[i] * arr[mid] < arr[i] + arr[mid]:                
                l = mid + 1
            else:
                r = mid - 1    
    
    return count
a = [0.5, 1.2, 2, 5, 8.5, 100, 110]
result = count_pairs(a)
print(result)
