## web2py_lazy_options_widget.py

This plugin is derived from plugin_lazy_options_widget.py from Kenji Hosoda <hosoda@s-cubism.jp>

Ref.: https://github.com/scubism/sqlabs/blob/master/modules/plugin_lazy_options_widget.py

I renamed it web2py_lazy_options_widget.py

It been customized to support select (reference) type field with multiple selected element.
It been extend to support chained conditional field, so once dependent conditional field get populated there a jquery
trigger event triggered so the next dependent field get updated and ready to be populated.
This plugin also prevent too many data to be pull form the database at the initial page load. The dependant conditional
field get it data only once the conditional field get populated through ajax call as proper filtering can occurs.
This reduce the page loading time and the backend overhead associate with this plugin.

**How to use it :**
Place the plugin in your modules/ folder and import it where you need it like this :

from web2py_lazy_options_widget import lazy_options_widget

**NOTE:** It not been port to py3 yet...

Any contributions is welcome

This plugins is licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

**Disclaimers:** This is provided "as is", without warranty of any kind.
