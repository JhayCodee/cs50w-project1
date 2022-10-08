# cs50w-project1
En este proyecto, construirás un sitio web para reseñas de libros. Los usuarios serán capaces de registrarse en tu sitio web e iniciar sesión usando su nombre de usuario y contraseña. Una vez hayan iniciado sesión, serán capaces de buscar libros, y ver las reseñas hechas por otras personas. También usarás una API de terceros, hecha por Google Books, otro sitio web para reseñas de libros, para obtener calificaciones de una audiencia más amplia. Finalmente, los usuarios serán capaces de consultar detalles y reseñas de libros programáticamente a través de la API de tu sitio web.

## Requerimientos del proyecto:

### - Registro: 
Los usuarios deberían ser capaces de registrarse en tu sitio web, proveyendo (como mínimo) un nombre de usuario y una contraseña. (**Se encuentra en application.py, en la ruta /register**).

### - Inicio de Sesión: 
Los usuarios, una vez registrados, deberían ser capaces de iniciar sesión en tu sitio web con su nombre de usuario y contraseña.  (**Se encuentra en application.py, en la ruta /login**).

### - Cierre de sesión: 
Los usuarios conectados deberían ser capaces de cerrar sesión. (**Se encuentra en application.py, en la ruta /logout**).

### - Importar:
Se le proporciona en este proyecto un archivo llamado books.csv, el cual es una hoja de cálculo en formato CSV de 5000 libros diferentes. Cada uno tiene un número ISBN, un título, un autor, y un año de publicación. En un archivo Python llamado import.py separado de tu aplicación web, escriba un programa que tome los libros y los importe a su base de datos PostgreSQL. Primero necesitarás decidir qué tablas crear, qué columnas esas tablas deberían tener, y cómo se deberían relacionar entre ellas (**se encuentra en import.py**)

#### Diagrama de la BD:
[![bd](https://i.postimg.cc/QCBwrr04/p1.png "bd")](http://https://i.postimg.cc/QCBwrr04/p1.png "bd")

### - Búsqueda: 
Una vez que el usuario ha iniciado sesión, deberían ser llevados a una página donde puedan buscar un libro. Los usuarios deberían ser capaces de ingresar el número ISBN de el libro, el título de el libro, o el autor de un libro. Luego de realizar la búsqueda, tu sitio web debería mostrar una lista de posibles coincidencias, o alguna clase de mensaje si no hubieron coincidencias. Si el usuario ingresó solamente parte de un título, ISBN, o nombre del autor, ¡tu página de búsqueda debería encontrar coincidencias para esos igualmente! **(Se encuentra en "/" index )**

### - Pagina de Libro 
Cuando los usuarios hagan click en un libro entre los resultados de la página de búsqueda, deberían ser llevados a una página de libro, con detalles sobre el libro: su título, autor, año de publicación, número ISBN, y cualquier reseña que los usuarios han dejado para ese libro en tu sitio web.  **(Se encuentra en la ruta /book en application.py )**

### - Envío de Reseña:
En la página de libro, los usuarios deberían ser capaces de enviar una reseña: consistiendo en un puntaje en una escala del 1 al 5, al igual que un componente de texto para la reseña donde el usuario pueda escribir su opinión sobre un libro. Los usuarios no deberían ser capaces de enviar múltiples reseñas para el mismo libro.  **(Se encuentra en la ruta /book en application.py )**

### - Información de Reseña de Goodreads (Google Books API): 
En la página de libro, también deberías mostrar (si está disponible) el puntaje promedio y cantidad de puntuaciones que el libro ha recibido de Goodreads. **(Se encuentra en la ruta /book en application.py )**

### - Acceso a API: 
Si los usuarios hacen una solicitud GET a la ruta /api/ de tu sitio web, donde es un número ISBN, tu sitio web debería retornar una respuesta JSON conteniendo el título del libro, autor, fecha de publicación, número ISBN, conteo de reseñas, y puntaje promedio. El JSON resultante debería seguir el siguiente formato:
                        
                {
                    "title": "Memory",
                    "author": "Doug Lloyd",
                    "year": 2015,
                    "isbn": "1632168146",
                    "review_count": 28,
                    "average_score": 5.0
                }
				
Si el número ISBN solicitado no está en tu base de datos, tu sitio web debería retornar un error 404.
**(Se encuentra en la ruta /api en application.py y en errorhandler 404 )**

