/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

var Backbone = require('backbone');


var UserProfileRouter = Backbone.Router.extend({

  routes: {
    '': 'main',
    'edit(/)': 'edit',
  },

});


module.exports = UserProfileRouter;
