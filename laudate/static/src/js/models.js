odoo.define('laudate.models', function (require) {
"use strict";

var models = require('point_of_sale.models');
var SuperOrder = models.Order;


models.Order = models.Order.extend({
    
    initialize: function(attributes,options){
        var self = this;
        SuperOrder.prototype.initialize.call(this,attributes,options);
        this.to_invoice = true;     
        return this;
    },
    
});
});