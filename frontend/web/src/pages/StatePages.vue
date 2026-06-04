<template>
<section class="page" id="stateLoadingPage">
        <div class="state-wrap">
          <div class="state-card">
            <div class="state-icon">✦</div>
            <h2>正在整理这一天</h2>
            <p>正在分析已授权的照片、位置和日程线索，预计还需 6 秒。</p>
            <div class="progress"><i></i></div>
            <div class="check-list">
              <div><span>读取照片元数据</span><b>完成</b></div>
              <div><span>匹配位置停留</span><b>完成</b></div>
              <div><span>生成日期回顾</span><b>进行中</b></div>
            </div><button class="primary" style="width:100%;margin-top:16px" data-go="reviewPage">查看整理结果</button>
          </div>
        </div>
      </section>
<section class="page" id="stateErrorPage">
        <div class="state-wrap">
          <div class="state-card">
            <div class="state-icon" style="color:var(--red);background:rgba(255,139,139,.1);border-color:rgba(255,139,139,.22)">!</div>
            <h2>部分线索未授权</h2>
            <p>当前无法读取 App 使用线索，因此只能基于照片、位置和日程生成较粗略的回顾。</p>
            <div class="grid-2" style="margin-top:16px"><button class="secondary" data-go="homePage">暂时跳过</button><button class="primary" data-go="permissionPage">去授权</button></div>
          </div>
        </div>
      </section>
<section class="page" id="stateEmptyPage">
        <div class="state-wrap">
          <div class="state-card">
            <div class="state-icon">☾</div>
            <h2>这一天线索太少</h2>
            <p>没有足够的照片、位置或日程记录来生成完整回顾。你可以切换日期，或手动补充一段记忆。</p><button class="primary" style="width:100%;margin-top:16px" data-go="calendarPage">换一天看看</button>
          </div>
        </div>
      </section>
<section class="page" id="stateSuccessPage">
        <div class="state-wrap">
          <div class="state-card">
            <div class="state-icon" style="color:var(--green);background:rgba(115,215,166,.1);border-color:rgba(115,215,166,.2)">✓</div>
            <h2>已收藏这段记忆</h2>
            <p>这段回忆已加入收藏。你之后可以通过日期或自然语言重新找到它。</p>
            <div class="grid-2" style="margin-top:16px"><button class="secondary" data-go="reviewPage">返回回顾</button><button class="primary" data-go="homePage">完成</button></div>
          </div>
        </div>
      </section>
</template>
