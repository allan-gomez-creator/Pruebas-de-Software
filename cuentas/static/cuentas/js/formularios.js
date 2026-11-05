// cuentas/static/cuentas/js/formularios.js — MEJORAS DE USABILIDAD.
// Son solo ayudas visuales: TODAS las reglas se validan en el servidor
// (cuentas/forms.py). Si el navegador tiene JavaScript desactivado, el
// sistema funciona igual.

// (function () { ... })(); es una función que se ejecuta de inmediato.
// Encierra las variables para que no se mezclen con otros scripts.
(function () {

  // ---------- 1. Botón "Ver / Ocultar" contraseña ----------
  // Busca todos los botones con la clase .ver-password (los pone _campo.html).
  document.querySelectorAll('.ver-password').forEach(function (boton) {
    boton.addEventListener('click', function () {
      // data-objetivo="id_password1" -> boton.dataset.objetivo es el id del input.
      var input = document.getElementById(boton.dataset.objetivo);
      if (!input) return;                               // si no existe, no hace nada
      var mostrar = input.type === 'password';          // ¿está oculta ahora?
      // Cambiar el type del input entre "password" (puntos) y "text" (visible).
      input.type = mostrar ? 'text' : 'password';
      boton.textContent = mostrar ? 'Ocultar' : 'Ver';  // texto del botón
      // aria-label: lo que anuncia un lector de pantalla.
      boton.setAttribute('aria-label', mostrar ? 'Ocultar contraseña' : 'Mostrar contraseña');
    });
  });

  // ---------- 2. Requisitos de la contraseña en vivo (página de registro) ----------
  // Busca la lista <ul data-requisitos-de="..."> de registro.html.
  document.querySelectorAll('[data-requisitos-de]').forEach(function (lista) {
    // dataset.requisitosDe lee el atributo data-requisitos-de (id del input a vigilar).
    var input = document.getElementById(lista.dataset.requisitosDe);
    if (!input) return;

    // Una función por regla. Cada una recibe el texto (v) y devuelve true si cumple.
    // Son las mismas reglas de CA-01.4 que valida el servidor.
    var reglas = {
      longitud: function (v) { return v.length >= 8; },   // 8 caracteres o más
      mayuscula: function (v) { return /[A-Z]/.test(v); }, // al menos una mayúscula
      minuscula: function (v) { return /[a-z]/.test(v); }, // al menos una minúscula
      numero: function (v) { return /[0-9]/.test(v); }     // al menos un número
    };

    // Recorre cada <li data-regla="..."> y le pone o quita la clase "cumple"
    // (el CSS la pinta de verde con ●).
    function actualizar() {
      lista.querySelectorAll('[data-regla]').forEach(function (li) {
        li.classList.toggle('cumple', reglas[li.dataset.regla](input.value));
      });
    }

    input.addEventListener('input', actualizar);   // se ejecuta con cada tecla
    actualizar();                                  // estado inicial al cargar la página
  });
})();