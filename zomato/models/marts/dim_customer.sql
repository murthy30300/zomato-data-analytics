select 
customer_id,
customer_name,
email,
age,
CASE WHEN age < 25 then "Gen Z"
        WHEN age >= 25 and age < 40 then "Millennials"
        WHEN age >= 40 and age < 55 then "Gen X"
        WHEN age is null then "Unknown"
        ELSE "Boomers" END as age_segment,
gender,
marital_status,
occupation,
income_band,
education,
family_size,

from {{ref('stg_users')}}