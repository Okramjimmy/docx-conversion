import redis

# Connect to Redis server
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

# Write data to Redis
redis_client.set('name', 'John Doe 1')  # Sets the key 'name' with value 'John Doe'

# Retrieve data from Redis
name = redis_client.get('name')

# Print the retrieved data
if name:
    print(f"Name from Redis: {name.decode('utf-8')}")
else:
    print("No data found for the key 'name'")
