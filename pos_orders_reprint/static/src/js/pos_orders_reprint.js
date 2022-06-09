// pos_orders_reprint js
odoo.define('pos_orders_reprint.pos_orders_reprint', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	var ActionManagerBrowseinfo = require('web.ActionManager');
	var PaymentScreenWidget = screens.PaymentScreenWidget;
	var QWeb = core.qweb;
	var rpc = require('web.rpc');
	var pos_orders_list = require('pos_orders_list.pos_orders_list');

	var _t = core._t;

    var ReceiptScreenWidgetNew = screens.ScreenWidget.extend({
		template: 'ReceiptScreenWidgetNew',
		
		init: function(parent, args) {
			this._super(parent, args);
			this.options = {};
		},

		show: function(options) {
			var self = this;
			options = options || {};
			self._super(options);

			var order = this.pos.get_order();
			var order_screen_params = order.get_screen_data('params');

			this.render_reprint_receipt();

			$('.button.back').on("click", function() {
				self.gui.show_screen('see_all_orders_screen_widget');
			});
			$('.button.print').click(function() {
				var test = self.chrome.screens.receipt;
				setTimeout(function() { self.chrome.screens.receipt.lock_screen(false); }, 1000);
				if (!test['_locked']) {
					self.chrome.screens.receipt.print_web();
					self.chrome.screens.receipt.lock_screen(true);
				}
			});
			
			$("#barcode_print1").barcode(
				order_screen_params['barcode'], // Value barcode (dependent on the type of barcode)
				"code128" // type (string)
			);
			
			if (self.should_auto_print()) {
				// window.print();
				setTimeout(function(){
					window.print();
					return;
				}, 500);
			}
			
		},

		render_reprint_receipt: function() {
			this.$('.pos-receipt-container').html(QWeb.render('OrderReceipt1', this.get_reprint_receipt_render_env()));
		},

		should_auto_print: function() {
			return this.pos.config.iface_print_auto && !this.pos.get_order()._printed;
		},

		get_reprint_receipt_render_env: function() {
			var order = this.pos.get_order();
			var order_screen_params = order.get_screen_data('params');
			return {
				widget: order_screen_params['widget'],
				order:  order_screen_params['order'],
				paymentlines: order_screen_params['paymentlines'],
				orderlines:  order_screen_params['orderlines'],
				discount_total:  order_screen_params['discount_total'],
				change:  order_screen_params['change'],
				subtotal:  order_screen_params['subtotal'],
				tax:  order_screen_params['tax'],
				barcode: order_screen_params['barcode'],
			};
		},
	});
	gui.define_screen({ name: 'ReceiptScreenWidgetNew', widget: ReceiptScreenWidgetNew });


	// pos_orders_list start

	pos_orders_list.include({
		
		show: function(options) {
			var self = this;
			this._super(options);

			this.details_visible = false;

			var orders = self.pos.get('all_orders_list');;
			this.render_list_orders(orders, undefined);

			this.$('.back').click(function(){
				//self.gui.back();
				self.gui.show_screen('products');
			});
			self.$('.orders-list-contents').delegate('.print-order', 'click', function(result) {
				result.stopImmediatePropagation();
				var order_id = parseInt(this.id);
				orders = self.pos.get('all_orders_list');
				var orderlines = [];
				var paymentlines = [];
				var discount = 0;
				var subtotal = 0;
				var tax = 0;
				var barcode;

				var selectedOrder = null;
				for(var i = 0, len = Math.min(orders.length,1000); i < len; i++) {
					if (orders[i] && orders[i].id == order_id) {
						selectedOrder = orders[i];
					}
				}
				
				rpc.query({
					model: 'pos.order',
					method: 'print_pos_receipt',
					args: [order_id],
				
				}).then(function(output) {
					orderlines = output[0];
					paymentlines = output[2];
					discount = output[1];
					subtotal = output[4];
					tax = output[5];
					barcode = output[6];
					self.pos.set({'reprint_barcode' : barcode});
					self.gui.show_screen('ReceiptScreenWidgetNew',{
						'widget':self,
						'order': selectedOrder,
						'paymentlines': paymentlines,
						'orderlines': orderlines,
						'discount_total': discount,
						'change': output[3],
						'subtotal': subtotal,
						'tax': tax,
						'barcode':barcode,
					});
					
				});
				return;
			});

		},
		should_auto_print: function() {
			return this.pos.config.iface_print_auto && !this.pos.get_order()._printed;
		},
	});
	
	

});
