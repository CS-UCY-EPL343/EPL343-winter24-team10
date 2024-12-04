import os
import mysql.connector
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = 'root'
DB_PASSWORD = 'rootpassword'
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    """Establish a connection to the database."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        collation="utf8mb4_general_ci",
    )

def drop_tables():
    """Drop the tables in the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                conn.commit() 

                cursor.execute("DROP TABLE IF EXISTS NOTIFICATIONS;")
                conn.commit()

                # cursor.execute("DROP TABLE IF EXISTS STOCK;")
                # conn.commit()

                # cursor.execute("DROP TABLE IF EXISTS ACCOUNTS;")
                # conn.commit()

                # cursor.execute("DROP TABLE IF EXISTS USER_ROLE;")
                # conn.commit()

                # cursor.execute("DROP TABLE IF EXISTS ROLE;")
                # conn.commit()

                # cursor.execute("DROP TABLE IF EXISTS USER;")
                # conn.commit()

                # cursor.execute("DROP TABLE IF EXISTS news_articles;")
                # conn.commit()

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                conn.commit()  

        logging.info("\n\nTables dropped successfully.\n\n")

    except mysql.connector.Error as e:
        logging.error(f"Database error: {str(e)}")
        logging.error("Stack trace: " + traceback.format_exc())
        return {"Error_Message": f"An error occurred while dropping the tables: {str(e)}"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        logging.error("Stack trace: " + traceback.format_exc())
        return {"Error_Message": f"An unexpected error occurred: {str(e)}"}
    
    
def create_tables():
    """Create the necessary tables in the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INT(11) AUTO_INCREMENT PRIMARY KEY,
                    source_id VARCHAR(255),
                    source_name VARCHAR(255),
                    author VARCHAR(255),
                    title VARCHAR(255),
                    description TEXT,
                    url TEXT,
                    url_to_image TEXT,
                    published_at DATETIME,
                    content TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """)
                conn.commit()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS USER (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    lvl INT NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    last_logged_in DATETIME,
                    status VARCHAR(50),
                    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
                """)
                conn.commit()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ROLE (
                    role_id INT AUTO_INCREMENT PRIMARY KEY,
                    role_name VARCHAR(100) NOT NULL,
                    role_description TEXT
                );
                """)
                conn.commit()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS USER_ROLE (
                    user_id INT NOT NULL,
                    role_id INT NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES ROLE(role_id) ON DELETE CASCADE
                );
                """)
                conn.commit()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ACCOUNTS (
                    account_id INT AUTO_INCREMENT PRIMARY KEY,
                    state VARCHAR(100) NOT NULL,
                    user_id INT NOT NULL UNIQUE,
                    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE
                );
                """)
                conn.commit()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS STOCK (
                    stock_id INT AUTO_INCREMENT PRIMARY KEY,
                    stock_name VARCHAR(100) NOT NULL,
                    date DATE NOT NULL,
                    open_price DECIMAL(10, 2),
                    close_price DECIMAL(10, 2),
                    high_price DECIMAL(10, 2),
                    low_price DECIMAL(10, 2),
                    value DECIMAL(15, 2)
                );
                """)
                conn.commit()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS NOTIFICATIONS (
                    notification_id INT AUTO_INCREMENT PRIMARY KEY,
                    threshold DECIMAL(10, 2) NOT NULL,
                    user_id INT NOT NULL,
                    stock_id INT NOT NULL,
                    date_created DATE DEFAULT CURRENT_DATE NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (stock_id) REFERENCES STOCK(stock_id) ON DELETE CASCADE
                );
                """)
                conn.commit()

        logging.info("Tables created successfully.")

    except mysql.connector.Error as e:
        logging.error(f"Database error: {str(e)}")
        logging.error("Stack trace: " + traceback.format_exc())
        return {"Error_Message": f"An error occurred while creating the tables: {str(e)}"}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        logging.error("Stack trace: " + traceback.format_exc())
        return {"Error_Message": f"An unexpected error occurred: {str(e)}"}
    
def create_all_stored_procedures():
    # Establish connection to the database
    connection = get_db_connection()
    
    cursor = connection.cursor()

    # SQL to create all stored procedures
    create_procedures_sql = """
-- AuthenticateUser Procedure
CREATE PROCEDURE AuthenticateUser(
    IN p_email VARCHAR(255),
    IN p_password VARCHAR(255))
BEGIN
    DECLARE user_count INT;

    -- Check if the user exists with the given email and password
    SELECT COUNT(*) INTO user_count
    FROM USER
    WHERE email = p_email AND password = p_password;

    IF user_count = 1 THEN
        SELECT 'Authentication successful' AS message;
    ELSE
        SELECT 'Invalid email or password' AS message;
    END IF;
END$$

-- CreateAccount Procedure
CREATE PROCEDURE CreateAccount(  
    IN p_email VARCHAR(255),
    IN p_password VARCHAR(255),
    IN p_username VARCHAR(50),
    IN p_status VARCHAR(50),
    IN p_lvl INT
)
BEGIN 
    DECLARE user_exists INT DEFAULT 0;

    -- Check if the user with the given email already exists
    SELECT COUNT(*) INTO user_exists
    FROM USER
    WHERE email = p_email;

    -- If the user exists, exit the procedure with a message
    IF user_exists > 0 THEN
        SELECT 'Error: Email already exists' AS message;
        LEAVE;
    END IF;

    -- Insert the new user into the USER table
    INSERT INTO USER (email, password, username, status, lvl)
    VALUES (p_email, p_password, p_username, p_status, p_lvl);

    -- Optionally, retrieve and return the new user ID
    SELECT LAST_INSERT_ID() AS new_user_id;

    -- Return a success message
    SELECT 'Account created successfully' AS message;
END$$

-- CalculateStockPercentageChange Procedure
CREATE PROCEDURE CalculateStockPercentageChange(IN start_date DATE, IN end_date DATE)
BEGIN
    SELECT stock_name, 
        (MAX(close_price) - MIN(open_price)) / MIN(open_price) * 100 AS percentage_change
    FROM STOCK
    WHERE date BETWEEN start_date AND end_date
    GROUP BY stock_name;
END$$

-- FindMostPopularStock Procedure
CREATE PROCEDURE FindMostPopularStock()
BEGIN
    SELECT stock_id, COUNT(*) AS notification_count
    FROM NOTIFICATIONS
    GROUP BY stock_id
    ORDER BY notification_count DESC
    LIMIT 1;
END$$

-- GetLatestStockId Procedure
CREATE PROCEDURE GetLatestStockId(
    IN p_stock_name VARCHAR(100),
    OUT p_stock_id INT
)
BEGIN
    -- Retrieve the stock ID for the most up-to-date instance of the given stock name
    SELECT stock_id
    INTO p_stock_id
    FROM STOCK
    WHERE stock_name = p_stock_name
    ORDER BY date DESC
    LIMIT 1;

    -- Raise an error if stock is not found
    IF p_stock_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Stock not found for the given name';
    END IF;
END$$
    """

    try:
        cursor.execute(create_procedures_sql)
        connection.commit()
        print("Stored procedures created successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()
