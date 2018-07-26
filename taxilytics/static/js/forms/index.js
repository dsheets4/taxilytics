define(
    [
        'js/forms/info_form',
        'js/forms/filter_form',
        'js/forms/help_form',
        'js/forms/cubeset_form',
    ],
function(info, filter, help, cubeset) {
    return {
        Info: info,
        Filter: filter,
        Help: help,
        CubeSet: cubeset
    }
});
