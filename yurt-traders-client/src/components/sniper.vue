<template>
  <section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          WSS Provider
        </p>
      </div>
      <div class="card-content">
        <div class="content">
          <b-field label="WSS Provider">
            <b-input v-model="providerAddress" required
                     validation-message="Please enter a WSS provider"
                     pattern="^wss.*" expanded></b-input>
          </b-field>
          <b-button v-on:click="chooseWSS()"
                    expanded>
            Save WSS
          </b-button>
        </div>

      </div>

    </section>
    <section v-if="provider" class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Contract Function Sniper
        </p>
      </div>
      <div class="card-content">
        <div class="content">
          <b-field label="Token Address">
            <b-input v-model="contract_address" required
                     validation-message="Please provide a valid 42 character long hexadecimal (0x...) value"
                     pattern="0x[a-fA-F0-9]{40}" expanded></b-input>
          </b-field>
          <b-field label="Interacting Address (owner automatically)">
            <b-input v-model="owner" required
                     expanded></b-input>
          </b-field>
          <b-field label="ABI">
            <b-input v-model="contract_abi" required
                     validation-message="Token ABI"
                     expanded></b-input>
          </b-field>
          <b-field v-if="abiList !== {}" label="Function selector">
            <b-select expanded v-model="method" placeholder="Select a function">
              <option

                  v-for="option in abiList"
                  :value="option"
                  :key="option.id">
                {{ option.name }}
              </option>
            </b-select>
          </b-field>
          <article v-if="contract_name" class="message">
            <div class="message-body">
              <strong>Contract: </strong> {{ contract_name }} - {{ symbol }} - <a target="_blank"
                                                                                  :href="blockchain.scanner + 'address/' + contract_address">{{
                blockchain.scanner_name
              }}</a>
            </div>
            <div v-if="this.methodId" class="message-body mt-3">
              <strong>Method ID: </strong> {{ this.methodId }}
            </div>
          </article>

          <b-button v-on:click="getInfo()"
                    expanded>
            Analyse Contract
          </b-button>
          <b-button class="mt-3" v-if="contract_abi" v-on:click="methodId ? methodId = null :generateMethodId()"
                    expanded>
            {{ this.methodId ? 'Unlock Method' : 'Lock Selected Method' }}
          </b-button>
          <b-button :type="listening ? 'is-danger' : 'is-info'" v-if="contract_abi" class="mt-3" v-on:click="listener()"
                    expanded>
            {{ this.listening ? 'Stop Listening' : 'Start Listening' }}
          </b-button>e
        </div>
      </div>
    </section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Sniper
        </p>
      </div>

      <div class="card-content">
        <div class="content">
          <div class="columns">


          </div>


          <b-button
              expanded>
            Buy
          </b-button>

          <p class="has-text-centered mt-1">
            {{ this.sniper.workerInfo }}
          </p>

        </div>
      </div>
    </section>
  </section>
</template>

<script>
import tokenAbi from "../assets/token_abi"
import uniAbi from "../assets/uni_abi"
import uniFactoryAbi from "../assets/uni_factory_abi"
import pairAbi from "../assets/pair_abi"
import {ethers} from "ethers";

export default {
  name: 'Sniper',
  props: {
    'socket': {},
    'wallets': {},
    'blockchain': {
      default() {
        return {
          price: null, symbol: '', network: '', scanner: '', scanner_name: ''
        }
      }
    },
    'web3': {}
  },
  computed: {
    abiList() {
      return this.contract_abi.length > 10 ? JSON.parse(this.contract_abi).filter(function (obj) {
        return obj.stateMutability !== 'view';
      }) : [];

    },
  },
  watch: {},
  data: function () {
    return {
      contract_address: '',
      tokenAbi: tokenAbi,
      uniAbi: uniAbi,
      uniFactoryAbi: uniFactoryAbi,
      pairAbi: pairAbi,
      contract: null,
      contract_abi: '',
      router: null,
      factory: null,
      contract_name: false,
      symbol: false,
      error: false,
      sniper: {},
      method: {},
      methodId: null,
      owner: '*',
      provider: null,
      providerAddress: localStorage.getItem('providerAddress') || '',
      listening: false,
      addresses: {'0x10ED43C718714eb63d5aA57B78B54704E256024E': ['PancakeSwap V2', 'Router']}
    }
  },
  filters: {
    abbreviateNumber(value) {
      var suffixes = ["", "K", "M", "B", "T"];
      var suffixNum = Math.floor(("" + value).length / 3);
      var shortValue = parseFloat((suffixNum !== 0 ? (value / Math.pow(1000, suffixNum)) : value).toPrecision(3));
      if (shortValue % 1 !== 0) {
        shortValue = shortValue.toFixed(2);
      }
      return shortValue + suffixes[suffixNum];
    },
    toUSD(value) {
      return value.toString().match(/[0-9]*\.0*[1-9]{0,1}[0-9]{0,3}/)[0]
    }
  },
  created() {
    this.contract_address = localStorage.getItem("sniper_ca")
  },
  methods: {
    chooseWSS() {
      this.provider = new ethers.providers.WebSocketProvider(this.providerAddress);
      localStorage.setItem('providerAddress', this.providerAddress)
    },
    listener() {
      if (this.listening) {
        this.provider.off('block')
        this.listening = false;
      } else {
        this.listening = true;
        this.provider.on("block", (blockNumber) => {
          this.provider.getBlockWithTransactions(blockNumber).then(function (result) {
            console.log("New block detected. No:", result.number);
            console.log("Block timestamp", new Date(result.timestamp * 1000));
            console.log("Current timestamp", new Date());
            const filteredTransactions = result.transactions.filter((item) => {
              if (this.methodId) {
                if (!item.data.startsWith(this.methodId)) {
                  return false;
                }
              }
              if (this.owner !== '*') {
                if (!item.from !== this.owner) {
                  return false;
                }
              }
              return true;
            });
            console.log(filteredTransactions);
          }.bind(this));
        })
      }

    },
    async generateMethodId() {
      this.methodId = this.web3.eth.abi.encodeFunctionSignature(this.method);
    },
    async getInfo() {
      if (/^0x[a-fA-F0-9]{40}$/.test(this.contract_address)) {
        this.contract = new this.web3.eth.Contract(this.tokenAbi, this.contract_address);
        this.router = new this.web3.eth.Contract(this.uniAbi, this.blockchain.router);
        this.factory = new this.web3.eth.Contract(this.uniFactoryAbi, this.blockchain.factory)
        try {
          if (!this.addresses[this.contract_address]) {
            this.symbol = await this.contract.methods.symbol().call();
            this.contract_name = await this.contract.methods.name().call();
          } else {
            this.contract_name = this.addresses[this.contract_address][0]
            this.symbol = this.addresses[this.contract_address][1]
          }
          try {
            this.owner = await this.contract.methods.getOwner().call();
          } catch (e) {
            console.log(e)
          }

          const apiRequestURL = 'https://api.bscscan.com/api?module=contract&action=getabi&address=' + this.contract_address + '&apikey=' + '84FD3JWWAJGQJH84HFB5PPPVXRWDTE7W8V'
          const apiResponse = await (await fetch(apiRequestURL)).json();
          console.log(apiResponse.result)
          this.contract_abi = apiResponse.result;
          localStorage.setItem("sniper_ca", this.contract_address)

        } catch (e) {
          this.$buefy.toast.open({
            duration: 5000,
            message: `Error: address provided is not a token or you are on the wrong network.`,
            position: 'is-top',
            type: 'is-danger'
          })
          this.contract_name = false
        }

      } else {
        this.contract_name = false
      }

    },
    buy() {
      this.socket.emit('buy', {
        amount: this.sniper.buyAmount,
        wallets: this.sniper.walletCount,
        repeat: this.sniper.repeat,
        contract: this.contract_address
      })
    },

  }
  ,
}
/*
    async simulateBuy() {
      const path = [this.blockchain.token, this.contract_address];
      console.log(path);
      const nowInSeconds = Math.floor(Date.now() / 1000)
      const expiryDate = nowInSeconds + 900;
      const result = await this.router.methods.swapExactETHForTokens(
          0,
          path,
          this.wallets[0].address,
          expiryDate
      ).call({
        from: this.wallets[0].address,
        gasLimit: 5000000,
        gasPrice: this.web3.utils.toWei("10", "gwei"),
        value: this.web3.utils.toWei("0.001", "ether")
      })
      console.log("Buy:", result);
      this.actualPrice = result[0] / result[1] * 10 ** -18;
      if (this.price_as_bnb !== 1) {
        this.tax = this.actualPrice / this.price_as_bnb;
        console.log(this.tax);
      }

    },
 */
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
