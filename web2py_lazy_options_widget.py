# -*- coding: utf-8 -*-

"""
This plugin is derived from plugin_lazy_options_widget.py from Kenji Hosoda <hosoda@s-cubism.jp>
Ref.: https://github.com/scubism/sqlabs/blob/master/modules/plugin_lazy_options_widget.py

I renamed it web2py_lazy_options_widget.py

It been customized to support select (reference) type field with multiple selected element.
It been extend to support chained conditional field, so once dependent conditional field get populated there a jquery
trigger event triggered so the next dependent field get updated and ready to be populated.
This plugin also prevent too many data to be pull form the database at the initial page load. The dependant conditional
field get it data only once the conditional field get populated through ajax call as proper filtering can occurs.
This reduce the page loading time and the backend overhead associate with this plugin.

How to use it :
Place the plugin in your modules/ folder and import it where you need it like this :

from web2py_lazy_options_widget import lazy_options_widget

NOTE: It not been port to py3 yet, any contribution is welcome.

This plugins is licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

      Author : Richard Vézina
       Email : ml.richard.vezina@gmail.com
   Copyright : Richard Vézina
        Date : 20 mars 2018 15:04
 Disclaimers : This is provided "as is", without warranty of any kind.
"""

from gluon import *


class lazy_options_widget(SQLFORM.widgets.options):

    def __init__(self,
                 on_key,
                 off_key,
                 where,
                 trigger=None,  # Rename this attribute
                 suggest_widget=True,  # In case you don't want to use plugin_suggest_widget, set suggest_widget to
                 # False. In this case, this piece of js with be including :
                 # $("select[name=<CONDITIONAL_FIELD_NAME>]").change(function() {
                 #     var val = $(this).children(":selected").attr("value");
                 #     $(this).trigger($(this).attr("id") + "__selected", [val]);
                 #     });
                 # Where <CONDITIONAL_FIELD_NAME> will be replaced with the field name of the
                 # conditional field name.
                 widget_chained=False,  # In case the widget field is also a conditional field for another widget field
                 # you need to trigger event like "WIDGET_FIELD_NAME__selected" when the widget
                 # field option is finally selected
                 widget_trigger_event_js=None,  # If you need to trigger something when the widget field option is
                 # finally selected you can pass a piece of js here that will be injected
                 # into the form when the conditional field trigger event "__selected"
                 default='---',
                 keyword='_lazy_options_%(fieldname)s',
                 orderby=None,
                 user_signature=False,
                 hmac_key=None,
                 row=None,  # In order to set values and filtered drop down appropriately based on values of
                 # conditional and widget field when the form is populated. Since you can't get row like this
                 # Field(..., widget=lambda field, value, row: ...
                 # When form is populated (update form) you need to define a row object base on the id of
                 # the record like this :
                 # row = db(db.table.id = request.vars.id).select(db.table.ALL).first()
                 # and pass it to lazy_option_widget...
                 ):
        self.on_key = on_key
        self.off_key = off_key
        self.where = where
        self.trigger = trigger
        self.default = default
        self.keyword = keyword
        self.orderby = orderby
        self.user_signature = user_signature
        self.hmac_key = hmac_key
        self.row = row
        self.suggest_widget = suggest_widget
        self.widget_trigger_event_js = widget_trigger_event_js
        self.widget_chained = widget_chained

        if self.suggest_widget:
            self.suggest_widget = 'true'
        else:
            self.suggest_widget = 'false'

        # if field:
        #     self.process_now(field)

    def _get_select_el(self, trigger, value=None):
        ret = (self.default, [OPTION('', _value='')])
        # Let return empty option tag on initial page load to properly filter out unrequired records to avoid pulling
        # out all the database records of the implicated referenced tables
        if trigger:
            trigger_event_selected = SCRIPT('''$(function() {
                        $("#%(aux_tag_id)s").change(function() {
                            var val = $(this).children(":selected").attr("value");
                            $("#%(tag_id)s").trigger("%(tag_id)s__selected", [val]);
                            });
                        });''' % {'aux_tag_id': self._el_id + '__aux', 'tag_id': self._el_id})
            widget_trigger_event_js = SCRIPT(self.widget_trigger_event_js)
            self._require.orderby = self.orderby or self._require.orderby
            self._require.dbset = self._require.dbset(self.where(trigger))
            options = self._require.options()
            opts = [OPTION(v, _value=k) for (k, v) in options]
            # multiple = {}
            # if self._require.multiple is True:
            #     multiple['_multiple'] = 'multiple'
            ret = (DIV(SELECT(_id='%s__aux' % self._el_id,
                              value=value,
                              _onchange='jQuery("#%s").val(jQuery(this).val());' % self._hidden_el_id,
                              *opts,
                              **self.multiple),
                       trigger_event_selected if self.widget_chained is True else '',
                       widget_trigger_event_js if self.widget_trigger_event_js is not None else ''),
                   SELECT(*opts,
                          value=value,
                          _name=self.fieldname,
                          _id=self._hidden_el_id,
                          _style='display: none;',
                          **self.multiple),
                   opts)
            # If conditional field is trigger we now return 3 different things, 2 up to date select elements the
            # visible and hidden one the up to date options to be used to populate selects update form page load.
        return ret

    def _pre_process(self, field):
        self._keyword = self.keyword % dict(fieldname=field.name)
        self.fieldname = field.name
        self._el_id = '%s_%s' % (field._tablename, field.name)
        self._disp_el_id = '%s__display' % self._el_id
        self._hidden_el_id = '%s__hidden' % self._el_id

        requires = field.requires

        if isinstance(requires, IS_EMPTY_OR):
            requires = requires.other
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            if hasattr(requires[0], 'options'):
                self._require = requires[0]
            else:
                raise SyntaxError('widget cannot determine options of %s' % field)
        else:
            self._require = []
        self.multiple = {}
        if self._require.multiple is True:
            self.multiple['_multiple'] = 'multiple'

    def process_now(self, field):
        if not hasattr(self, '_keyword'):
            self._pre_process(field)

        if self._keyword in current.request.vars:
            if self.user_signature:
                if not URL.verify(current.request, user_signature=self.user_signature, hmac_key=self.hmac_key):
                    raise HTTP(400)

            trigger = current.request.vars[self._keyword]
            raise HTTP(200, [str(i) for i in self._get_select_el(trigger)[0:2]])  # We only need the select elements
        return self

    def __call__(self, field, value, **attributes):
        self._pre_process(field)

        request = current.request
        if hasattr(request, 'application'):
            self.url = URL(r=request, args=request.args,
                           user_signature=self.user_signature, hmac_key=self.hmac_key)
            self.process_now(field)
        else:
            self.url = request

        # --------------------------------------------------------------------------------------------------------------
        # The script is responsible of all further update over html elements once the initial page load occurs
        script_el = SCRIPT("""
            jQuery(document).ready(function() {

                jQuery("body").on("%(on_key)s", function(e, val) {
                    jQuery("#%(disp_el_id)s").html("%(default)s");
                    jQuery("#%(hidden_el_id)s option:selected").prop("selected", false);
                    var query = {}
                    query["%(keyword)s"] = val;
                    jQuery.ajax({type: "POST", url: "%(url)s", data: query,
                        success: function(html) {
                          html = html.split();
                          // Since we return 2 select items now we need to split the obtained ajax string
                          jQuery("#%(disp_el_id)s").html(html[0]);
                          jQuery("#%(hidden_el_id)s").html(html[1]);
                          // We assign each select with slicing over html array we get after split ajax string
                    }});
                });
                jQuery("body").on("%(off_key)s", function(e) {
                    jQuery("#%(disp_el_id)s").html("%(default)s");
                    jQuery("#%(hidden_el_id)s option:selected").prop("selected", false);
                });
                var suggest_widget = '%(suggest_widget)s'
                if (suggest_widget == 'false') {
                    $("select#%(conditional_field_name)s").change(function() {
                        var val = $(this).children(":selected").attr("value");
                        $(this).trigger($(this).attr("id") + "__selected", [val]);
                        });
                    }
            });""" % dict(on_key=self.on_key,
                          off_key=self.off_key,
                          disp_el_id=self._disp_el_id,
                          hidden_el_id=self._hidden_el_id,
                          default=self.default,
                          keyword=self._keyword,
                          url=self.url,
                          suggest_widget=self.suggest_widget,
                          conditional_field_name=self.on_key[0:-10]
                          ))
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # The code below is for initial page load widget initialization
        if value and self.row and current.request.vars.keyword is None:
            select_el, select_hidden, options = self._get_select_el(trigger=self.row[self.off_key[0:-12]])
        else:
            select_el, select_hidden, options = \
                self._get_select_el(self.trigger, value) if self.trigger else (None, None, [OPTION('', _value='')])
        el = DIV(script_el,
                 SPAN(select_el or self.default,
                      SELECT(*options,
                             value=value,
                             _name=field.name,
                             _id=self._hidden_el_id,
                             _style='display: none;',
                             **self.multiple),
                      value=value,
                      _id=self._disp_el_id),
                 _id=self._el_id)
        # We had to move the hidden select inside the span in order to get it properly updated script_el jquery code
        # --------------------------------------------------------------------------------------------------------------
        return el
