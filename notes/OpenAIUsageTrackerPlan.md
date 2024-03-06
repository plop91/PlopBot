# plan for OpenAI Usage Tracker

## Database schema
database name: openai

### usernames_table
a table to store the usernames of the users
- id: int (Primary key) the id of the record
- username: string the username of the user
- date_created: date the date the user was created

### cost_table
a table to store the cost of each endpoint on openai
- endpoint: int (Primary key)(foreign key) the id of the endpoint
- date: date the last date the price was updated
- cost: float the cost of the function per request in dollars on openai

### endpoint_table
a table to store the name of the endpoints
- id: int (primary key) the id of the record
- endpoint_name: string (unique) the name of the function

 initial data:
 openai_images_generate
 openai_images_variation
 openai_assistant_create
 openai_assistant_submit_tool_run
 openai_assistant_thread_create
 openai_assistant_run

### assistant_table
list of assistants created by users, including the creator username, assistant id, and the date created
- id: int (primary key) the id of the record
- creator_id: int (foreign key) the username of the creator
- assistant_id: string (unique) the id of the assistant

### thread_table
list of threads created by users, including the creator username, thread id, and the date created
- id: int (primary key) the id of the record
- creator_username: string (foreign key) the username of the creator
- thread_id: string (unique) the id of the thread

### endpoint_usage_table
a table to store the usage of each endpoint on openai
- id: int (primary key) the id of the record
- endpoint: string (foreign key) the name of the endpoint
- date: date the date of the last usage
- usage: int the number of requests made on that date
- cost: float the cost of the requests made on that date

### endpoint_user_usage_table
a table to store the usage of each endpoint by each user
- id: int (primary key) the id of the record
- endpoint: string (foreign key) the name of the endpoint
- username: string (foreign key) the username of the user
- date: date the date of the last usage
- usage: int the number of requests made on that date
- cost: float the cost of the requests made on that date

### blacklisted_user_table
a table to store the blacklisted users
- id: int (primary key) the id of the record
- user_id: int (foreign key) the user_id of the user
- date: date the date the user was blacklisted
- reason: string the reason the user was blacklisted
- blacklisted_by: int (foreign key) the user_id of the user who blacklisted the user
- blacklisted_until: date the date the user will be blacklisted until

### rate_limited_user_table
a table to store the rate limited users
- id: int (primary key) the id of the record
- user_id: int (foreign key) the user_id of the user
- date: date the user was rate limited
- reason: string the reason the user was rate limited
- rate_limited_by: int (foreign key) the user_id of the user who rate limited the user
- rate_limited_until: date the date the user will be rate limited until
- rate_limit: int the number of requests the user is limited to



