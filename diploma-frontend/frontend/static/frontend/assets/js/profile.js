var mix = {
    methods: {
        getProfile() {
            this.getData('/api/profile')
                .then(data => {
                    this.fullName = data.fullName
                    this.avatar = data.avatar
                    this.phone = data.phone
                    this.email = data.email
                })
                .catch(() => console.warn('Ошибка профиля'))
        },

        saveAll() {
            this.errors = {}

            const profilePromise = this.postData('/api/profile', {
                fullName: this.fullName,
                email: this.email,
                phone: this.phone,
            })

            const hasPassword = this.passwordCurrent || this.password || this.passwordReply
            const passwordPromise = hasPassword
                ? this.postData('/api/profile/password', {
                    currentPassword: this.passwordCurrent,
                    newPassword: this.password,
                })
                : Promise.resolve()

            Promise.all([profilePromise, passwordPromise])
                .then(() => {
                    this.showToast('Изменения сохранены')
                    this.passwordCurrent = ''
                    this.password = ''
                    this.passwordReply = ''
                })
                .catch((err) => {
                    const errors = err?.response?.data?.errors
                    this.errors = errors || {general: 'Ошибка сохранения'}
                })
        },

        setAvatar(event) {
            const file = event.target.files[0]
            if (!file) return

            const formData = new FormData()
            formData.append('avatar', file)

            this.postData('/api/profile/avatar', formData, {'Content-Type': 'multipart/form-data'})
                .then(() => this.getProfile())
                .catch(() => console.warn('Ошибка аватара'))
        },

        clearAvatar() {
            this.avatar = null
        },
    },

    created() {
        this.getProfile()
    },

    data() {
        return {
            fullName: null,
            phone: null,
            email: null,
            avatar: null,
            password: '',
            passwordCurrent: '',
            passwordReply: '',
            errors: {},
        }
    },
}
