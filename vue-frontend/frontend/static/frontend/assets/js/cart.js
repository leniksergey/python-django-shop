var mix = {
    methods: {
        submitBasket() {
            // Защита от двойного клика
            if (this.creatingOrder) return
            this.creatingOrder = true

            this.postData('/api/orders', Object.values(this.basket))
                .then(({data: {orderId}}) => {
                    location.assign(`/order-detail/${orderId}/`)
                })
                .catch(() => {
                    console.warn('Ошибка при создании заказа')
                    this.creatingOrder = false
                })
        }
    },
    mounted() {},
    data() {
        return {
            creatingOrder: false,
        }
    }
}
