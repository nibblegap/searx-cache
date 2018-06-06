/**
 * searx is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * searx is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with searx. If not, see < http://www.gnu.org/licenses/ >.
 *
 * (C) 2014 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
 */

$(document).ready(function() {
    /**
     * focus element if class="autofocus" and id="q"
     */
    // document.querySelector("#q[autofocus]").focus();
    $('#q[autofocus]').focus();

    /**
     * select full content on click if class="select-all-on-click"
     */
    $(".select-all-on-click").click(function () {
        $(this).select();
    });    

    /**
     * change text during btn-collapse click if possible
     */
    $('.btn-collapse').click(function() {
        var btnTextCollapsed = $(this).data('btn-text-collapsed');
        var btnTextNotCollapsed = $(this).data('btn-text-not-collapsed');
        
        if(btnTextCollapsed !== '' && btnTextNotCollapsed !== '') {
            if($(this).hasClass('collapsed')) {
                new_html = $(this).html().replace(btnTextCollapsed, btnTextNotCollapsed);
            } else {
                new_html = $(this).html().replace(btnTextNotCollapsed, btnTextCollapsed);
            }
            $(this).html(new_html);
        }
    });

    /**
     * change text during btn-toggle click if possible
     */
    $('.btn-toggle .btn').click(function() {
        var btnClass = 'btn-' + $(this).data('btn-class');
        var btnLabelDefault = $(this).data('btn-label-default');
        var btnLabelToggled = $(this).data('btn-label-toggled');
        if(btnLabelToggled !== '') {
            if($(this).hasClass('btn-default')) {
                new_html = $(this).html().replace(btnLabelDefault, btnLabelToggled);
            } else {
                new_html = $(this).html().replace(btnLabelToggled, btnLabelDefault);
            }
            $(this).html(new_html);
        }
        $(this).toggleClass(btnClass);
        $(this).toggleClass('btn-default');
    });
	
	/**
     * change text during btn-toggle click if possible
     */
    $('.media-loader').click(function() {
        var target = $(this).data('target');
        var iframe_load = $(target + ' > iframe');
        var srctest = iframe_load.attr('src');
        if(srctest === undefined || srctest === false){
            iframe_load.attr('src', iframe_load.data('src'));
        }
    });


    // kinda hack, to make the more categories menu work, when JS is enabled.
    $("#show_more_categories_").click(function(event) {
        $(event.target).addClass("hidden");
        $("#show_less_categories_").removeClass("hidden");
        $("#more_categories_toggle_").attr("checked", true);
    });
    $("#show_less_categories_").click(function(event) {
        $(event.target).addClass("hidden");
        $("#show_more_categories_").removeClass("hidden");
        $("#more_categories_toggle_").attr("checked", false);
    });
    $("#show_more_categories_").removeClass("hidden");
    $('<div id="more_categories_toggle_" class="hidden"></div>').insertAfter($("#more_categories_toggle"));
    $("#more_categories_toggle, #show_more_categories, #show_less_categories").remove();
});
