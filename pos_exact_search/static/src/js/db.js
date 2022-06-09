odoo.define('pos_exact_search.DB', function (require) {
"use strict";

var PosDB = require('point_of_sale.DB');
var utils = require('web.utils');

var PosDB = PosDB.include({
    init: function(options){
        this._super(options);           
        this.product_by_default_code = {};
    },
    
    add_products: function(products){
        var stored_categories = this.product_by_category_id;

        if(!products instanceof Array){
            products = [products];
        }
        for(var i = 0, len = products.length; i < len; i++){
            var product = products[i];
            var search_string = utils.unaccent(this._product_search_string(product));
            var categ_id = product.pos_categ_id ? product.pos_categ_id[0] : this.root_category_id;
            product.product_tmpl_id = product.product_tmpl_id[0];
            if(!stored_categories[categ_id]){
                stored_categories[categ_id] = [];
            }
            stored_categories[categ_id].push(product.id);

            if(this.category_search_string[categ_id] === undefined){
                this.category_search_string[categ_id] = '';
            }
            this.category_search_string[categ_id] += search_string;

            var ancestors = this.get_category_ancestors_ids(categ_id) || [];

            for(var j = 0, jlen = ancestors.length; j < jlen; j++){
                var ancestor = ancestors[j];
                if(! stored_categories[ancestor]){
                    stored_categories[ancestor] = [];
                }
                stored_categories[ancestor].push(product.id);

                if( this.category_search_string[ancestor] === undefined){
                    this.category_search_string[ancestor] = '';
                }
                this.category_search_string[ancestor] += search_string; 
            }
            this.product_by_id[product.id] = product;
            if(product.barcode){
                this.product_by_barcode[product.barcode] = product;
            }
            if(product.default_code){
                this.product_by_default_code[product.default_code] = product;
            }
        }
    },
    
    get_product_by_ref: function(ref){
        if(this.product_by_default_code[ref]){
            return this.product_by_default_code[ref];
        } else {
            return undefined;
        }
    },
    
    search_product_exactly: function(category_id, query){
        try {
            query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
            query = query.replace(/ /g,'.+');
            var re = RegExp("([0-9]+):.*?"+utils.unaccent(query),"gi");
        }catch(e){
            return [];
        }
        var results = [];
        
        results.push(this.get_product_by_ref(query));               
        return results;
    },
});
    
return PosDB;

});