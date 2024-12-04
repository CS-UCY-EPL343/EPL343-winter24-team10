import os
from mysql.connector import connect, Error 
import mysql
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
    connection = None
    cursor = None
    try:
        # Establish connection to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # List of procedure names to drop
        procedure_names = [
            "AuthenticateUser",
            "CreateAccount",
            "CalculateStockPercentageChange",
            "FindMostPopularStock",
            "GetLatestStockId",
            "GetStockOpenPrices",
            "InsertNotification",
            "InsertStock",
            "ChangePassword",
            "GetStockPredictionByName",
            "GetStockValue",
            "ExchangeCurrency"
        ]

        # Drop existing procedures
        for proc in procedure_names:
            try:
                cursor.execute(f"DROP PROCEDURE IF EXISTS {proc}")
                connection.commit()
                logging.info(f"Dropped procedure if it existed: {proc}")
            except Error as e:
                logging.error(f"Error while dropping procedure {proc}: {e}")

        # List of stored procedure definitions
        stored_procedures = [
            """
            CREATE PROCEDURE AuthenticateUser(
                IN p_email VARCHAR(255),
                IN p_password VARCHAR(255)
            )
            BEGIN
                DECLARE user_count INT;

                SELECT COUNT(*) INTO user_count
                FROM `USER`
                WHERE email = p_email AND password = p_password;

                IF user_count = 1 THEN
                    SELECT 'Authentication successful' AS message;
                ELSE
                    SELECT 'Invalid email or password' AS message;
                END IF;
            END;
            """,
            """
            CREATE PROCEDURE CreateAccount(
                IN p_email VARCHAR(255),
                IN p_password VARCHAR(255),
                IN p_username VARCHAR(50),
                IN p_status VARCHAR(50),
                IN p_lvl INT
            )
            BEGIN
                DECLARE user_exists INT DEFAULT 0;

                SELECT COUNT(*) INTO user_exists
                FROM `USER`
                WHERE email = p_email;

                IF user_exists > 0 THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Error: Email already exists';
                ELSE
                    INSERT INTO `USER` (email, password, username, status, lvl)
                    VALUES (p_email, p_password, p_username, p_status, p_lvl);

                    SELECT LAST_INSERT_ID() AS new_user_id;
                END IF;
            END;
            """,
            """
            CREATE PROCEDURE CalculateStockPercentageChange(
                IN start_date DATE,
                IN end_date DATE
            )
            BEGIN
                SELECT stock_name,
                       (MAX(close_price) - MIN(open_price)) / MIN(open_price) * 100 AS percentage_change
                FROM STOCK
                WHERE date BETWEEN start_date AND end_date
                GROUP BY stock_name;
            END;
            """,
            """
            CREATE PROCEDURE FindMostPopularStock()
            BEGIN
                SELECT stock_id, COUNT(*) AS notification_count
                FROM NOTIFICATIONS
                GROUP BY stock_id
                ORDER BY notification_count DESC
                LIMIT 1;
            END;
            """,
            """
            CREATE PROCEDURE GetLatestStockId(
                IN p_stock_name VARCHAR(100),
                OUT p_stock_id INT
            )
            BEGIN
                SELECT stock_id
                INTO p_stock_id
                FROM STOCK
                WHERE stock_name = p_stock_name
                ORDER BY date DESC
                LIMIT 1;

                IF p_stock_id IS NULL THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Stock not found for the given name';
                END IF;
            END;
            """,
            """
            CREATE PROCEDURE GetStockOpenPrices(
                IN start_date DATE,
                IN end_date DATE,
                IN stock_name VARCHAR(100)
            )
            BEGIN
                SELECT 
                    stock_name, 
                    date, open_price
                FROM 
                    STOCK
                WHERE 
                    STOCK.stock_name = stock_name 
                    AND date BETWEEN start_date AND end_date
                ORDER BY date;
            END;
            """,
            """
            CREATE PROCEDURE InsertNotification(
                IN p_threshold DECIMAL(10, 2),
                IN p_user_id INT,
                IN p_stock_name VARCHAR(255)
            )
            BEGIN
                DECLARE stock_id INT;

                IF NOT EXISTS (SELECT 1 FROM USER WHERE user_id = p_user_id) THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'User does not exist';
                END IF;

                SELECT s.stock_id INTO stock_id
                FROM STOCK s
                WHERE s.stock_name = p_stock_name
                ORDER BY s.date DESC
                LIMIT 1;

                IF stock_id IS NULL THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Stock does not exist';
                END IF;

                INSERT INTO NOTIFICATIONS (threshold, user_id, stock_id)
                VALUES (p_threshold, p_user_id, stock_id);
            END;
            """,
            """
            CREATE PROCEDURE InsertStock(
                IN p_stock_name VARCHAR(100),
                IN p_date DATE,
                IN p_open_price DECIMAL(10, 2),
                IN p_close_price DECIMAL(10, 2),
                IN p_high_price DECIMAL(10, 2),
                IN p_low_price DECIMAL(10, 2),
                IN p_value DECIMAL(15, 2)
            )
            BEGIN
                INSERT INTO STOCK (stock_name, date, open_price, close_price, high_price, low_price, value)
                VALUES (p_stock_name, p_date, p_open_price, p_close_price, p_high_price, p_low_price, p_value);

                INSERT INTO STOCK (stock_name, date, open_price, close_price, high_price, low_price, value)
                VALUES ('USD', p_date, 1.00, 1.00, 1.00, 1.00, 1.00);
            END;
            """,
            """
            CREATE PROCEDURE ChangePassword(
                IN p_username VARCHAR(50),
                IN p_old_password VARCHAR(255),
                IN p_new_password VARCHAR(255)
            )
            BEGIN
                DECLARE user_count INT;

                SELECT COUNT(*) INTO user_count
                FROM USER
                WHERE username = p_username AND password = p_old_password;

                IF user_count = 0 THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Invalid username or old password';
                ELSE
                    UPDATE USER
                    SET password = p_new_password
                    WHERE username = p_username;
                END IF;
            END;
            """,
            """
            CREATE PROCEDURE GetStockPredictionByName(
                IN stock_name VARCHAR(100)
            )
            BEGIN
                DECLARE up_count INT DEFAULT 0;
                DECLARE down_count INT DEFAULT 0;
                DECLARE total_count INT DEFAULT 0;
                DECLARE current_price DECIMAL(10, 2);
                DECLARE stock_id INT;

                SELECT stock_id INTO stock_id
                FROM STOCK
                WHERE stock_name = stock_name
                ORDER BY date DESC
                LIMIT 1;

                IF stock_id IS NULL THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Stock not found';
                END IF;

                SELECT close_price INTO current_price
                FROM STOCK
                WHERE stock_id = stock_id
                ORDER BY date DESC
                LIMIT 1;

                IF current_price IS NULL THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Stock price not available';
                END IF;

                SELECT COUNT(*) INTO total_count
                FROM NOTIFICATIONS
                WHERE stock_id = stock_id;

                IF total_count = 0 THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'No notifications found for this stock';
                END IF;

                SELECT 
                    SUM(CASE WHEN threshold < current_price THEN 1 ELSE 0 END) AS up_count,
                    SUM(CASE WHEN threshold >= current_price THEN 1 ELSE 0 END) AS down_count
                INTO up_count, down_count
                FROM NOTIFICATIONS
                WHERE stock_id = stock_id;

                IF up_count > down_count THEN
                    SELECT 'The majority believe the stock will go up' AS prediction;
                ELSEIF down_count > up_count THEN
                    SELECT 'The majority believe the stock will go down' AS prediction;
                ELSE
                    SELECT 'The votes are split evenly' AS prediction;
                END IF;
            END;
            """,
            """
            CREATE PROCEDURE GetStockValue(
                IN p_stock_name VARCHAR(100),
                IN p_date DATE,
                OUT p_value DECIMAL(15, 2)
            )
            BEGIN
                DECLARE stock_count INT;

                SELECT COUNT(*) INTO stock_count
                FROM STOCK
                WHERE stock_name = p_stock_name AND date = p_date;

                IF stock_count = 0 THEN
                    SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Stock not found for the given name and date';
                ELSE
                    SELECT value INTO p_value
                    FROM STOCK
                    WHERE stock_name = p_stock_name AND date = p_date;
                END IF;
            END;
            """,
            """
            CREATE PROCEDURE ExchangeCurrency(
                IN currency_pair VARCHAR(10),
                IN amount DECIMAL(15, 2),
                OUT result DECIMAL(15, 2)
            )
            BEGIN
                DECLARE exchange_rate DECIMAL(10, 2);

                SELECT close_price INTO exchange_rate
                FROM STOCK
                WHERE stock_name = currency_pair
                ORDER BY date DESC
                LIMIT 1;

                IF exchange_rate IS NULL THEN
                    SET result = 0;
                    SELECT 'Exchange rate not found' AS message;
                ELSE
                    SET result = amount * exchange_rate;
                END IF;
            END;
<<<<<<< HEAD
            """,
            """ 
            CREATE PROCEDURE GetUserNotifications(
                        IN p_user_id INT
                    )
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM USER WHERE user_id = p_user_id) THEN
                            SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = 'User does not exist';
                        END IF;

                        SELECT n.notification_id,
                            n.threshold,
                            n.date_created,
                            s.stock_name,
                            s.close_price AS latest_price
                        FROM NOTIFICATIONS n
                        JOIN STOCK s ON n.stock_id = s.stock_id
                        WHERE n.user_id = p_user_id
                        ORDER BY n.date_created DESC;
                    END;
                    """,
                    """
                    CREATE PROCEDURE DeleteNotification(
                        IN p_notification_id INT
                    )
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM NOTIFICATIONS WHERE notification_id = p_notification_id) THEN
                            SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = 'Notification does not exist';
                        END IF;

                        DELETE FROM NOTIFICATIONS
                        WHERE notification_id = p_notification_id;
                    END;
=======
>>>>>>> f92386ca1c762dfdfb933ad59f5f054a25545e20
            """
        ]

        # Execute each stored procedure
        for procedure in stored_procedures:
            try:
                cursor.execute(procedure)
                connection.commit()
                logging.info("Stored procedure created successfully.")
            except Error as e:
                logging.error(f"Error while creating stored procedure: {e}")
                print(f"Error while creating stored procedure: {e}")

    except Error as err:
        logging.error(f"Error while connecting to the database: {err}")
        print(f"Error while connecting to the database: {err}")

    finally:
        if cursor:
            cursor.close()
        if connection:
<<<<<<< HEAD
            connection.close()
=======
            connection.close()




>>>>>>> f92386ca1c762dfdfb933ad59f5f054a25545e20
