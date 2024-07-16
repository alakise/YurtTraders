<template>
  <section class="mb-5">

    <b-collapse
        class="card"
        animation="slide"
        :open="false"
    >
      <template #trigger="props">
        <div
            class="card-header"
            role="button"
            aria-controls="contentIdForA11y3">
          <p class="card-header-title">
            Set Mnemonics
          </p>
          <a class="card-header-icon">
            <b-icon
                :icon="props.open ? 'menu-down' : 'menu-up'">
            </b-icon>
          </a>
        </div>
      </template>

      <div class="card-content">
        <div class="content">
          <b-field label="12-key mnemonics">
            <b-input v-model="ui.mnemonics"
                     placeholder="aria holy pinnacle potato malgorzata"
            ></b-input>
          </b-field>
        </div>
      </div>
      <footer class="card-footer">
        <a v-on:click="save_mnemonics()" class="card-footer-item">Save Mnemonics</a>
      </footer>
    </b-collapse>

  </section>
</template>

<script>
export default {
  name: 'mnemonic',
  props: ['ui', 'socket'],
  methods: {
    send(event, args) {
      this.socket.emit(event, args);
    },
    save_mnemonics() {
      this.send('set_mnemonic', {'mnemonic': this.ui.mnemonics})
    },
  },
}
</script>
