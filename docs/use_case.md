# Casos de uso

## Actores

- Empleado, lee correos electronicos desde la red interna.
- Administrador, configura la aplicacion.

## CU1: empleado hace login

El empleado se logeará en la nueva página web, desde la red interna sin acceso a internet. Utilizando para ello:
- su correo
- contraseña 
- servidor*
- puerto* 

en una web para donde podrá posteriormente visualizar los correos electronicos la red interna.

En caso de error deberá notificarse al usuario.
En caso de usar algún dato no habilitado por el administrador, se notificará al usuario y el incidente quedrá registrado.

## CU2: empleado visualiza la lista de correos

El empleado verá una lista con sus correos, donde distinguirá emisor, asunto, fecha de recepción y si fue leido o no.

## CU3: empledo lee un correo

El empleado podrá seleccionar un correo de la lista para poder leer el cuerpo del mensaje.
Una vez seleccionado el mensaje se marca como leído.

## CU4: administrador configura

El administrador a traves de un archivo de configuración puede habilitar qué servidores o que cuentas de correo electrónico pueden usarse desde la red interna.
