<template>
  <section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Network Settings
        </p>
      </div>
      <div class="card-content">
        <div class="content">
          <b-field label="Network">
            <b-select expanded v-model="user.active">
              <option value="BSC">Binance Smart Chain</option>
              <option value="AVAX">Avalanche</option>
              <option value="METIS">Metis</option>
              <option value="CRONOS">Cronos</option>
              <option value="MILKOMEDA">Milkomeda Cardano (C1)</option>
              <option value="BSC_testnet">Binance Smart Chain (testnet)</option>
              <option value="DOGECHAIN">Dogechain</option>
              <option value="ETC">Ethereum Classic</option>
              <option value="ETH">Ethereum</option>
              <option value="ETH_goerli">Ethereum Görli</option>

            </b-select>

          </b-field>
          <hr>
          <div class="columns">
            <div class="column">
              <b-field label="Telegram BOT token">
                <b-input v-model="user.bot_token"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Etherscan API token">
                <b-input v-model="user.etherscan_api"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Bscscan API token">
                <b-input v-model="user.bscscan_api"></b-input>
              </b-field>
            </div>
          </div>
           <div class="columns">
            <div class="column">
              <b-field label="Ethereum RPC">
                <b-input v-model="user.ETH_rpc"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="BSC RPC">
                <b-input v-model="user.BSC_rpc"></b-input>
              </b-field>
            </div>
          </div>

          <hr>
          <b-field label="Wallets">
            <b-input v-model="user.buy.wallets"></b-input>
          </b-field>
          <hr>
          <div class="columns">
            <div class="column">
              <b-field label="Buy Gas">
                <b-input v-model="user.gas.buy"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Sell Gas">
                <b-input v-model="user.gas.sell"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Approve Gas">
                <b-input v-model="user.gas.approve"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="All Other Gas">
                <b-input v-model="user.gas.all"></b-input>
              </b-field>
            </div>

          </div>
          <hr>
          <div class="buttons">
            <b-button v-on:click="save()" type="is-link is-outlined" expanded>Save Network AND Telegram Settings
            </b-button>
          </div>


        </div>
      </div>
    </section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Telegram Settings
        </p>
      </div>

      <div class="card-content">
        <div class="content">

          <b-field label="Whitelist (use enter)">
            <b-taginput v-model="whitelist"
            >
            </b-taginput>
          </b-field>
          <b-field label="Blacklist (use enter)">
            <b-taginput type="is-dark" v-model="blacklist"></b-taginput>
          </b-field>
          <b-field label="Telegram Scanner Orders">
            <b-input
                v-model="spaceSeperated"

                placeholder="t.me/asdasdasd*2x0.05*multi*single*wallets=5"
                type="textarea"
            >
            </b-input>
          </b-field>
          <aside class="menu">
            <ul class="menu-list">
              <li v-for="element in visual" :key="element.id">
                <a v-if="element.id === 0 ||visual[element['id'] - 1]['name'] !== element['name']" class="is-active"
                   v-html="element['name'] + element['tags']"></a>
                <ul>
                  <li><a v-html="element['order']"></a></li>
                </ul>
              </li>
            </ul>
          </aside>
          <hr>
          <div class="buttons">
            <b-button v-on:click="save()" type="is-link is-outlined" expanded>Save Network AND Telegram Settings
            </b-button>
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<script>

export default {
  name: 'Settings',
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
    'user': {
      "phone_number": null,
      "telegram": {
        "listen": '',
        "blacklist": '',
        "whitelist": ''
      },
      "buy": {"audit": false, "wallets": 2},
      "gas": {"buy": 5, "sell": 5, "approve": 5, "all": 5},
      "active": "BSC",
      'bot_token': '',
      'etherscan_api': 'YourApiToken',
      'bscscan_api': 'YourApiToken',
      'ETH_rpc': '',
      'bsc_rpc': ''
    }
  },
  watch: {},
  data: function () {
    return {
      telegrams: {}
    }
  },
  computed: {
    spaceSeperated: {
      get() {
        return this.user.telegram.listen.replace(/,/g, '\n')
      },
      // setter
      set(newValue) {
        this.user.telegram.listen = newValue.replace(/\n/g, ',')
      }

    },
    visual: {
      get() {
        let list = this.user.telegram.listen.split(',')
        let id = 0;
        list.forEach((item, index, arr) => {
          let tags = ' ';
          let el = arr[index];
          let order = 'Buy <b class="is-primary">';
          let name = ""
          if (el.match(/https:\/\/t.me\/([^*]*)\*/))
            name = '@' + el.match(/https:\/\/t.me\/([^*]*)\*/)[1];
          let groupId = el.match(/(?:-)([0-9]+)/);
          if (groupId && this.telegrams.length > 1) {
            let result = this.telegrams.filter(o => o.id.toString().includes(groupId[1]));
            if (result && result[0]) {
              name = result[0].name + '(' + groupId[1] + ')';
            }
          }
          if (el.match('alarm')) {
            tags += '<span class="tag is-danger">alarm</span> '
            el = el.replace('*alarm', '')
          }
          if (el.match('1p')) {
            tags += '<span class="tag is-dark">1%</span> '
            el = el.replace('*1p', '')
          }
          if (el.match('portal')) {
            tags += '<span class="tag is-dark">portal</span> '
            el = el.replace('*portal', '')
          }
          if (el.match('single')) {
            tags += '<span class="tag is-dark">single buy</span> '
            el = el.replace('*single', '')
          }
          let buy = el.match(/\*([1-9]+x[0-9.]+)/);
          if (buy) {
            order += buy[1]
            el = el.replace(/\*([1-9]+x[0-9.]+)/, '')
          } else {
            order += 'AMOUNT MISSING'
            tags += '<span class="tag is-danger">ERROR INCORRECT</span>'
          }
          order += '</b>'
          if (el.match('multi')) {
            let wallets = el.match(/\*wallets=([0-9]+)/);
            if (wallets) {
              order += ' with ' + wallets[1] + ' '
              el = el.replace(/\*wallets=([0-9]+)/, '')
            } else {
              order += ' with all wallets '
            }
            el = el.replace('*multi', '')
          } else {
            order += ' with first wallet '
          }
          let wallets = el.match(/\*mcap=([0-9]+)/);
          if (wallets) {
            order += 'under ' + wallets[1].replace(/000000$/, 'M').replace(/000$/, 'k') + ' market cap'
            el = el.replace(/\*mcap=([0-9]+)/, '')
          }
          console.log(el)
          arr[index] = {name: name, order: order, tags: tags, id: id};
          id++;
        });
        return list


      },
      // setter
      set(newValue) {
        this.user.telegram.listen = newValue.replace(/\n/g, ',')
      }

    },
    blacklist: {
      get() {
        return this.user.telegram.blacklist.split(',')
      },
      // setter
      set(newValue) {
        this.user.telegram.blacklist = newValue.join(',')
      }

    },
    whitelist: {
      get() {
        return this.user.telegram.whitelist.split(',')
      },
      // setter
      set(newValue) {
        this.user.telegram.whitelist = newValue.join(',')
      }

    }

  },

  methods: {
    save() {
      this.socket.emit('save_settings', this.user)
    }
  }
  ,
  mounted() {
    this.socket.on("dialogues", (e) => {
      console.log("Dialogue list refreshed.", e.dialogues)
      this.telegrams = e.dialogues;
    });
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
hr {
  background-color: darkslategray;
}

.has-addons .button {
  line-height: 0;
}
</style>
