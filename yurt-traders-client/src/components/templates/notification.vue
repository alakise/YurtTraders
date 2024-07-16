<template>
  <div class="notification-element">
    <b-message
        class="mb-2"
        :title="output.title"
        :type="output.type ? 'is-' + output.type : null"
    >
      <span v-html="output.message"></span>
      <span v-if="output.decision"><hr>
                    <span v-html="output.decision.info"></span>
                  </span>
      <b-collapse
          v-if="output.message_content"
          :open="false"
      >
        <template #trigger="props">
          <a>
            <b-icon :icon="!props.open ? 'menu-down' : 'menu-up'"></b-icon>
            {{ !props.open ? 'Show message content' : 'Hide message content' }}
          </a>
        </template>
        <p>
          {{ output.message_content }}</p>
      </b-collapse>
    </b-message>
    <div class="columns pb-0 mb-0" v-if="output.decision">
      <div :class="'column is-half pb-0 mb-0 ' + (output.decision.info.includes('not a contract') ? '' : 'pr-1')">
        <a v-if="output.decision.contract" target="_blank"
           :href="blockchain.scanner + 'address/' + output.decision.contract"
           class="button is-primary mb-2  is-fullwidth">
          {{ blockchain.scanner_name }} <span class="icon ml-1"><i
            class="mdi mdi-open-in-new mdi-24px"></i></span>
        </a>
      </div>
      <div v-if="output.decision.contract && !output.decision.info.includes('not a contract')"
           class="column is-half pl-1 pb-0 mb-0">
        <a target="_blank"
           :href="chart_link + output.decision.contract"
           class="button is-primary mb-2  is-fullwidth">
          Chart <span class="icon ml-1"><i
            class="mdi mdi-chart-line mdi-24px"></i></span>
        </a>
      </div>

    </div>
    <div v-if="output.decision.contract && !output.decision.info.includes('not a contract')"
         class="">
      <a target="_blank"
         v-on:click="$emit('setActiveContractAddress', output.decision.contract)"
         class="button is-primary mb-2  is-fullwidth">
        Token Interaction <span class="icon ml-1"><i
          class="mdi mdi-dots-horizontal-circle-outline mdi-24px"></i></span>
      </a>
    </div>

  </div>
</template>
<script>
export default {
  props: ['output', 'blockchain'],
  computed: {
    chart_link() {
      try {
        switch (this.blockchain.network) {
          case "bsc":
            return 'https://poocoin.app/tokens/'
          case "eth":
            return 'https://www.dextools.io/app/ether/pair-explorer/'
          default:
            return 'https://dexscreener.app/' + this.blockhain.network + '/'
        }
      } catch (e) {
        return 'https://poocoin.app/tokens/'
      }

    }
  }
}
</script>