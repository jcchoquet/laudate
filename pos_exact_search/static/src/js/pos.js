odoo.define('pos_exact_search', function (require) {
"use strict";

    var screens = require('point_of_sale.screens');    
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;    

    screens.ProductCategoriesWidget.include({
        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            var search_timeout  = null;
            this.search_handler2 = function(event){
                if(event.type == "keypress" || event.keyCode === 46 || event.keyCode === 8){
                    clearTimeout(search_timeout);

                    var searchbox = this;

                    search_timeout = setTimeout(function(){
                        self.perform_search2(self.category, searchbox.value, event.which === 13);
                    },70);
                }
            };
        },
        renderElement: function(){
            var self = this;
            this._super();
            if(self.pos.config.allow_exact_search){
                this.el.querySelector('.searchbox2 input').addEventListener('keypress',this.search_handler2);
                this.el.querySelector('.searchbox2 input').addEventListener('keydown',this.search_handler2);
            }
        },
        clear_search2: function(){
            var products = this.pos.db.get_product_by_category(this.category.id);
            this.product_list_widget.set_product_list(products);
            var input = this.el.querySelector('.searchbox2 input');
                input.value = '';
                input.focus();
        },
        perform_search2: function(category, query, buy_result){
            var products;
            var product_list = [];
            if(query){
                products = this.pos.db.search_product_exactly(category.id,query);
                _.each(products, function(product){
                    if (product['barcode'] == query || product['default_code'] == query || product['display_name'] == query ){
                        product_list.push(product)    
                    }
                });
                products = product_list
                if(buy_result && products.length === 1){
                        this.pos.get_order().add_product(products[0]);
                        this.clear_search2();
                }else{
                    this.product_list_widget.set_product_list(products);
                }
            }else{
                products = this.pos.db.get_product_by_category(this.category.id);
                this.product_list_widget.set_product_list(products);
            }
        },
    });
    
    
});

