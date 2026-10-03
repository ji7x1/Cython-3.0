/* Cython 3.0 - كود مشترك بين الصفحات.
 * لازم ينحمل بالـ <head> قبل الـ <body> حتى الثيم يتطبق قبل ما تظهر الصفحة (بدون وميض).
 */
(function (window) {
    'use strict';

    function read(key) {
        try { return window.localStorage.getItem(key); } catch (e) { return null; }
    }

    /* يطبق الوضع (dark/light) واللون المحفوظين من الصفحة الرئيسية.
     * options (كلها اختيارية، كل صفحة تحافظ على سلوكها القديم):
     *   mode  - الوضع الافتراضي اذا ماكو شي محفوظ (مثلاً 'dark')
     *   color - اللون الافتراضي اذا ماكو شي محفوظ (مثلاً 'color-1')
     *   dark / light - لون خلفية <html> بكل وضع (اذا ما انطوه، ما تنلمس الخلفية)
     */
    function apply(options) {
        var o = options || {};
        var root = window.document.documentElement;
        var mode = read('themeMode') || o.mode;
        var color = read('themeColor') || o.color;
        if (mode === 'dark') root.classList.add('dark');
        if (color) root.classList.add(color);
        if (o.dark && o.light) root.style.backgroundColor = mode === 'dark' ? o.dark : o.light;
        return { mode: mode, color: color };
    }

    window.CythonTheme = { apply: apply };
})(window);
