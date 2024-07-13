# Bus Management System
#### Video Demo:  [Link to video](https://youtu.be/4azjykUFrLc)
## Description
The Bus Management System web application which would be used by institutions to manage bus operations efficiently. This system is developed from Flask, along with SQL for database management. The objective of this application is to facilitate the management of buses, drivers, conductors, and trip records for school administrations, ensuring smooth operations.

## Features

### Bus Management
The web application can handle detailed management of school buses. Users can add, remove, and update bus records. Each bus record has information such as the route number, registration number, driver's name, conductor's name, and the number of students thus ensuring that all bus-related data is easily accessible and manageable.

### Trip Records
This feature of the Bus Management System maintains and tracks trip records. Each trip record includes details like the route number, trip number, the number of students who got on and off the bus, the distance covered, and the in and out times of the buses from the campus / institution. This helps in monitoring the bus operations and ensures that all trips are documented.

### Daily Reports
The application provides functionality to generate daily reports of the bus operations. This report includes all the necessary details such as route numbers, trip numbers, students in and out, distance covered, and in and out times of the buses. The reports can be downloaded as CSV files, making it easy to share and analyze the data.

## Tech Stack
### Backend
-> Flask: The primary web framework used for developing the application.
<br>
-> SQL: For database management.
<br>
-> Jinja2: Template engine for rendering HTML pages.

### Frontend
-> HTML: Markup language for creating web pages.
<br>
-> CSS: Styling the web pages.
<br>
-> JavaScript: For adding interactivity to the web pages.

## Project Structure
In the root directory, 
<br>
<br>
-> `app.py` It manages routes, stores data to SQL database and redirects to different pages of the web app. It is the heart of the project.
<br>
-> `project.db` The database where all information regarding the user and the buses is stored.
<br>
-> `requirements.txt` Contains the dependencies required to run this project.
<br>
<br>
In the `/static` folder, CSS file is stored which makes the web app look pretty and the `favicon.ico ` which is the favicon used.
<br>
<br>
In the `/templates` folder, reside all `.html` files.
<br>
<br>
->`layout.html` Which contains the basic layout of the site and can be used as a template for other `.html` files
<br>
->`add_bus.html` Which helps the user to add a bus into the database
<br>
->`remove_bus.html` Which allows the user to remove a bus from the database
<br>
->`update_bus.html` Which enables the user to update information of a bus in the database.
<br>
->`index.html` Which shows all the data of the buses in the database
<br>
->`pending_buses.html` Which shows all the buses outside the campus and are yet to arrive.
<br>
->`maintain_records.html` Which allows users to start maintaining records of buses going in and out of campus
<br>
->`register.html` and `login.html` Provide a form for users to login and register for the web app
<br>
->`apology.html` Which is a apology page when something goes wrong in the webpage. Adapted from CS50 Finance.
