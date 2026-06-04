<template>
<section class="page" id="searchPage">
        <div class="section-title">
          <h2>帮我想起</h2><span>自然语言记忆搜索</span>
        </div>
        <div class="searchbox"><input id="searchEntryInput" value="" autocomplete="off" placeholder="输入想要找回的记录"><button id="searchEntryBtn">搜</button></div>
        <div class="search-intro">
          <h3>输入想回忆的事，找回往日记录</h3>
          <p>点击上方搜索框后，可以像搜索视频一样输入线索，LifeTrace 会从日期回顾、照片、地点和日程里匹配相关片段。</p>
          <div class="search-examples"><span class="example-chip">晚霞</span><span class="example-chip">上次去图书馆</span><span class="example-chip">和朋友散步</span></div>
        </div>
        <div class="search-panel" id="searchPanel">
          <div class="search-panel-bar"><button class="search-panel-back" id="searchPanelBack">‹</button><input id="searchInput" value="" autocomplete="off" placeholder="输入想找回的记忆"><button id="searchBtn">搜索</button></div>
          <div id="searchGuide">
            <div class="search-block">
              <div class="search-block-head"><h3>猜你想搜</h3><span>根据近期线索</span></div>
              <div class="search-chip-grid"><button class="search-chip hot">晚霞</button><button class="search-chip hot">图书馆之后去了哪</button><button class="search-chip">最近一次散步</button><button class="search-chip">小组作业是哪天</button></div>
            </div>
            <div class="search-block">
              <div class="search-block-head"><h3>搜索历史</h3><span>清空</span></div>
              <div class="search-chip-grid"><button class="search-chip">图书馆</button><button class="search-chip">校园照片</button><button class="search-chip">和朋友聊天</button><button class="search-chip">晚上散步</button></div>
            </div>
            <div class="search-block">
              <div class="search-block-head"><h3>搜索发现</h3><span>换一换</span></div>
              <div class="search-discovery"><button>5 月的高光时刻</button><button>最近常去地点</button><button>有照片的日子</button><button>学习状态变化</button></div>
            </div>
          </div>
          <div id="searchResults"></div>
        </div>
      </section>
</template>
